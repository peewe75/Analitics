import os
from fastapi import APIRouter, Request, HTTPException, Depends
from svix.webhooks import Webhook, WebhookVerificationError
from sqlalchemy.orm import Session
from app.database import get_db
from app import models

router = APIRouter(prefix="/webhooks/clerk", tags=["webhooks"])

CLERK_WEBHOOK_SECRET = os.getenv("CLERK_WEBHOOK_SECRET")
DEFAULT_TENANT_ID = os.getenv("DEFAULT_TENANT_ID", "softi")

@router.post("")
async def clerk_webhook(request: Request, db: Session = Depends(get_db)):
    if not CLERK_WEBHOOK_SECRET:
        raise HTTPException(status_code=500, detail="Webhook secret not configured")

    headers = request.headers
    payload = await request.body()

    svix_id = headers.get("svix-id")
    svix_timestamp = headers.get("svix-timestamp")
    svix_signature = headers.get("svix-signature")

    if not svix_id or not svix_timestamp or not svix_signature:
        raise HTTPException(status_code=400, detail="Missing svix headers")

    wh = Webhook(CLERK_WEBHOOK_SECRET)
    try:
        # Verify the webhook
        evt = wh.verify(payload, {
            "svix-id": svix_id,
            "svix-timestamp": svix_timestamp,
            "svix-signature": svix_signature
        })
    except WebhookVerificationError:
        raise HTTPException(status_code=400, detail="Invalid signature")

    event_type = evt.get("type")
    data = evt.get("data", {})
    
    user_id = data.get("id")
    
    if event_type == "user.created" or event_type == "user.updated":
        email = None
        email_addresses = data.get("email_addresses", [])
        if email_addresses:
            # Try to get the primary email
            primary_id = data.get("primary_email_address_id")
            for em in email_addresses:
                if em.get("id") == primary_id:
                    email = em.get("email_address")
                    break
            if not email and email_addresses:
                email = email_addresses[0].get("email_address")
                
        user = db.query(models.User).filter(models.User.id == user_id).first()
        if not user:
            user = models.User(
                id=user_id,
                email=email,
                tenant_id=DEFAULT_TENANT_ID
            )
            db.add(user)
        else:
            user.email = email
            
        db.commit()

    elif event_type == "user.deleted":
        user = db.query(models.User).filter(models.User.id == user_id).first()
        if user:
            db.delete(user)
            db.commit()

    return {"success": True}
