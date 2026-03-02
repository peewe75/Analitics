from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
import app.models as models
from typing import List

router = APIRouter(prefix="/api/v1/admin", tags=["admin-management"])

@router.get("/users")
def list_users(db: Session = Depends(get_db)):
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
                "expires_at": u.subscription.current_period_end if u.subscription else None
            }
        })
    return results

@router.get("/payments/pending")
def list_pending_payments(db: Session = Depends(get_db)):
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
            "created_at": p.created_at,
            "payment_type": p.payment_type
        })
    return results

@router.get("/stats")
def get_admin_stats(db: Session = Depends(get_db)):
    """ Quick stats for the dashboard """
    total_users = db.query(models.User).count()
    pro_users = db.query(models.Subscription).filter(models.Subscription.plan != "LITE", models.Subscription.status == "ACTIVE").count()
    pending_payments = db.query(models.Payment).filter(models.Payment.status == "PENDING").count()
    
    return {
        "total_users": total_users,
        "pro_users": pro_users,
        "pending_payments": pending_payments
    }
