from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import app.models as models

def get_subscription(db: Session, user_id: str) -> models.Subscription:
    sub = db.query(models.Subscription).filter(models.Subscription.user_id == user_id).first()
    if not sub:
        # Auto-create LITE subscription for new users
        sub = models.Subscription(user_id=user_id, plan=models.PlanType.LITE, status=models.SubStatus.ACTIVE)
        db.add(sub)
        db.commit()
        db.refresh(sub)
    return sub

def request_pro_plan(db: Session, user_id: str, plan_type: str) -> models.Subscription:
    if plan_type not in [models.PlanType.PRO_MONTHLY, models.PlanType.PRO_YEARLY]:
        raise ValueError("Invalid plan type. Must be PRO_MONTHLY or PRO_YEARLY.")

    sub = get_subscription(db, user_id)
    
    # If already active PRO, prevent downgrade/upgrade through this simple flow for MVP
    if sub.status == models.SubStatus.ACTIVE and sub.plan != models.PlanType.LITE:
        if sub.current_period_end and sub.current_period_end > datetime.utcnow():
            raise ValueError(f"User already has an active {sub.plan} subscription.")
    
    sub.plan = plan_type
    sub.status = models.SubStatus.PENDING
    db.commit()
    db.refresh(sub)
    return sub

def activate_subscription(db: Session, subscription: models.Subscription, payment_type: str) -> models.Subscription:
    """ Called when a payment is VERIFIED. """
    now = datetime.utcnow()
    
    # Determine the length of the extension
    days_to_add = 30 if subscription.plan == models.PlanType.PRO_MONTHLY else 365
    
    if payment_type == models.PaymentType.INITIAL:
        subscription.current_period_start = now
        subscription.current_period_end = now + timedelta(days=days_to_add)
        subscription.renewals_count = 0
    elif payment_type == models.PaymentType.RENEWAL:
        # Extend from the current end date if it's a direct renewal within grace period
        if subscription.current_period_end and subscription.current_period_end > now:
            subscription.current_period_end = subscription.current_period_end + timedelta(days=days_to_add)
        else:
            # Should theoretically be a reactivation if passed grace period, but handle gracefully
            subscription.current_period_end = now + timedelta(days=days_to_add)
        subscription.renewals_count += 1
    elif payment_type == models.PaymentType.REACTIVATION:
        subscription.current_period_start = now
        subscription.current_period_end = now + timedelta(days=days_to_add)
        subscription.renewals_count += 1
        
    subscription.status = models.SubStatus.ACTIVE
    db.commit()
    db.refresh(subscription)
    return subscription
