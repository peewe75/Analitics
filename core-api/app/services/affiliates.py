from sqlalchemy.orm import Session
import app.models as models
import uuid

def create_affiliate(db: Session, user_id: str) -> models.Affiliate:
    # Check if already affiliate
    affiliate = db.query(models.Affiliate).filter(models.Affiliate.user_id == user_id).first()
    if affiliate:
        return affiliate
        
    # Generate unique ref code
    ref_code = str(uuid.uuid4())[:8].upper()
    affiliate = models.Affiliate(user_id=user_id, ref_code=ref_code)
    db.add(affiliate)
    db.commit()
    db.refresh(affiliate)
    return affiliate

def register_referral(db: Session, referred_user_id: str, ref_code: str):
    """ Record a first-touch attribution. Called during user registration if a ref code is present. """
    # Verify ref code exists
    affiliate = db.query(models.Affiliate).filter(models.Affiliate.ref_code == ref_code).first()
    if not affiliate:
        return False # Invalid ref code, ignore silently
        
    # Check if user already referred (immutable first touch)
    existing = db.query(models.Referral).filter(models.Referral.referred_user_id == referred_user_id).first()
    if existing:
        return False
        
    referral = models.Referral(affiliate_id=affiliate.id, referred_user_id=referred_user_id)
    db.add(referral)
    db.commit()
    return True

def process_commission(db: Session, payment: models.Payment):
    """ Calculate and generate pending commissions when a payment is VERIFIED. """
    if payment.status != "VERIFIED":
        return
        
    user_id = payment.subscription.user_id
    
    # 1. Check if user is referred
    referral = db.query(models.Referral).filter(models.Referral.referred_user_id == user_id).first()
    if not referral:
        return # No affiliate to pay
        
    affiliate_id = referral.affiliate_id
    
    # 2. Get affiliate rates (tenant default for now)
    tenant_id = payment.subscription.user.tenant_id
    settings = db.query(models.AffiliateSetting).filter(models.AffiliateSetting.tenant_id == tenant_id).first()
    
    if not settings:
        # Fallback default hardcoded defaults
        rate_initial_m = 0.20
        rate_initial_y = 0.20
        rate_renewal_m = 0.10
        rate_renewal_y = 0.10
        rate_reactivation_m = 0.10
        rate_reactivation_y = 0.10
    else:
        rate_initial_m = settings.rate_initial_monthly
        rate_initial_y = settings.rate_initial_yearly
        rate_renewal_m = settings.rate_renewal_monthly
        rate_renewal_y = settings.rate_renewal_yearly
        rate_reactivation_m = settings.rate_reactivation_monthly
        rate_reactivation_y = settings.rate_reactivation_yearly
    
    # 3. Determine rate
    rate = 0.0
    p_plan = payment.subscription.plan
    p_type = payment.payment_type
    
    if p_type == models.PaymentType.INITIAL:
        rate = rate_initial_m if p_plan == models.PlanType.PRO_MONTHLY else rate_initial_y
    elif p_type == models.PaymentType.RENEWAL:
        rate = rate_renewal_m if p_plan == models.PlanType.PRO_MONTHLY else rate_renewal_y
    elif p_type == models.PaymentType.REACTIVATION:
        rate = rate_reactivation_m if p_plan == models.PlanType.PRO_MONTHLY else rate_reactivation_y
        
    commission_amount = payment.amount * rate
    
    if commission_amount <= 0:
        return
        
    # 4. Create Commission record
    commission = models.Commission(
        affiliate_id=affiliate_id,
        payment_id=payment.id,
        amount=commission_amount,
        commission_type=p_type,
        status="PENDING" # Will move to APPROVABLE via a cron/job after `hold_days`
    )
    
    db.add(commission)
    db.commit()
