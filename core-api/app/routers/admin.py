from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.dependencies import get_db, get_current_admin
import app.models as models
from datetime import datetime, timedelta, timezone

router = APIRouter(prefix="/admin", tags=["admin-management"])

@router.get("/users")
def list_users(db: Session = Depends(get_db), current_admin: models.AdminUser = Depends(get_current_admin)):
    """ List all users with their subscription plans """
    users = db.query(models.User).all()
    results = []
    for u in users:
        results.append({
            "id": u.id,
            "email": u.email,
            "tenant_id": u.tenant_id,
            "subscription": {
                "plan": u.subscription.plan if u.subscription else "LITE",
                "status": u.subscription.status if u.subscription else "NONE",
                "expires_at": str(u.subscription.current_period_end) if u.subscription and u.subscription.current_period_end else None
            }
        })
    return results

@router.get("/payments/pending")
def list_pending_payments(db: Session = Depends(get_db), current_admin: models.AdminUser = Depends(get_current_admin)):
    """ List all payments waiting for admin approval """
    payments = db.query(models.Payment).filter(models.Payment.status == "PENDING").all()
    results = []
    for p in payments:
        results.append({
            "id": p.id,
            "user_email": p.subscription.user.email if p.subscription and p.subscription.user else "Unknown",
            "method": p.method,
            "amount": p.amount,
            "tx_reference": p.tx_reference,
            "created_at": str(p.created_at),
            "payment_type": p.payment_type
        })
    return results

@router.get("/stats")
def get_admin_stats(db: Session = Depends(get_db), current_admin: models.AdminUser = Depends(get_current_admin)):
    """ Quick stats for the dashboard """
    total_users = db.query(models.User).count()
    pro_users = db.query(models.Subscription).filter(models.Subscription.plan != "LITE", models.Subscription.status == "ACTIVE").count()
    pending_payments = db.query(models.Payment).filter(models.Payment.status == "PENDING").count()
    
    return {
        "total_users": total_users,
        "pro_users": pro_users,
        "pending_payments": pending_payments
    }

@router.post("/users/{user_id}/promote")
def promote_user_to_pro(
    user_id: str,
    db: Session = Depends(get_db),
    current_admin: models.AdminUser = Depends(get_current_admin)
):
    """ [ADMIN] Promote a user to PRO plan """
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Check if subscription exists
    sub = db.query(models.Subscription).filter(models.Subscription.user_id == user_id).first()
    
    now = datetime.now(timezone.utc)
    
    if sub:
        sub.plan = "PRO_MONTHLY"
        sub.status = "ACTIVE"
        sub.current_period_start = now
        sub.current_period_end = now + timedelta(days=30)
    else:
        sub = models.Subscription(
            user_id=user_id,
            plan="PRO_MONTHLY",
            status="ACTIVE",
            current_period_start=now,
            current_period_end=now + timedelta(days=30),
            renewals_count=0
        )
        db.add(sub)
    
    db.commit()
    return {"status": "success", "message": f"User {user.email} promoted to PRO"}

@router.post("/users/{user_id}/demote")
def demote_user_to_lite(
    user_id: str,
    db: Session = Depends(get_db),
    current_admin: models.AdminUser = Depends(get_current_admin)
):
    """ [ADMIN] Demote a user back to LITE plan """
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    sub = db.query(models.Subscription).filter(models.Subscription.user_id == user_id).first()
    if sub:
        sub.plan = "LITE"
        sub.status = "ACTIVE"
        sub.current_period_start = None
        sub.current_period_end = None
        db.commit()
    
    return {"status": "success", "message": f"User {user.email} demoted to LITE"}
