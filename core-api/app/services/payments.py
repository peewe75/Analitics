from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import app.models as models
from app.services.subscriptions import activate_subscription
import logging

def submit_payment(db: Session, user_id: str, method: str, amount: float, tx_reference: str) -> models.Payment:
    sub = db.query(models.Subscription).filter(models.Subscription.user_id == user_id).first()
    if not sub or sub.status != models.SubStatus.PENDING:
        raise ValueError("No pending PRO subscription found for user.")
        
    if method not in ["IBAN", "USDT", "STRIPE"]:
        raise ValueError("Invalid payment method.")

    # Determine payment type (INITIAL, RENEWAL, REACTIVATION)
    # LITE -> PRO is INITIAL
    # PRO -> Expired (< grace) -> PRO is RENEWAL
    # PRO -> Expired (> grace) -> PRO is REACTIVATION
    payment_type = models.PaymentType.INITIAL
    if sub.renewals_count > 0 or sub.current_period_end is not None:
        # Let's say grace period is 7 days, hardcoded for MVP (should be pulled from Affiliate settings or global settings)
        grace_days = 7
        if sub.current_period_end:
            expiration = sub.current_period_end.replace(tzinfo=None) # naive to naive compare
            now = datetime.utcnow()
            days_since_expiration = (now - expiration).days
            if days_since_expiration <= grace_days:
                payment_type = models.PaymentType.RENEWAL
            else:
                payment_type = models.PaymentType.REACTIVATION

    payment = models.Payment(
        subscription_id=sub.id,
        method=method,
        amount=amount,
        tx_reference=tx_reference,
        status="PENDING",
        payment_type=payment_type
    )
    
    db.add(payment)
    db.commit()
    db.refresh(payment)
    return payment

def verify_payment(db: Session, payment_id: int, admin_user_id: int) -> models.Payment:
    payment = db.query(models.Payment).filter(models.Payment.id == payment_id).first()
    if not payment:
        raise ValueError("Payment not found.")
        
    if payment.status == "VERIFIED":
        return payment # Idempotent

    payment.status = "VERIFIED"
    
    # 1. Activate the subscription
    sub = db.query(models.Subscription).filter(models.Subscription.id == payment.subscription_id).first()
    activate_subscription(db, sub, payment.payment_type)
    
    # 2. Trigger Affiliate Commissions (Defer to affiliate service)
    try:
        from app.services.affiliates import process_commission
        process_commission(db, payment)
    except Exception as e:
        logging.error(f"Failed to process commission for payment {payment.id}: {e}")
    
    # Audit log
    audit = models.AuditLog(
        admin_id=admin_user_id,
        action="VERIFY_PAYMENT",
        details=f"Payment {payment.id} verified. Subscription {sub.id} activated."
    )
    db.add(audit)
    db.commit()
    
    return payment

def reject_payment(db: Session, payment_id: int, admin_user_id: int, reason: str) -> models.Payment:
    payment = db.query(models.Payment).filter(models.Payment.id == payment_id).first()
    if not payment:
        raise ValueError("Payment not found.")

    payment.status = "REJECTED"
    
    # Audit log
    audit = models.AuditLog(
        admin_id=admin_user_id,
        action="REJECT_PAYMENT",
        details=f"Payment {payment.id} rejected. Reason: {reason}"
    )
    db.add(audit)
    db.commit()
    
    return payment
