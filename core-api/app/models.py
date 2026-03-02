from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Float, Text, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from .database import Base

class Tenant(Base):
    __tablename__ = "tenants"
    id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False)
    subdomain = Column(String, unique=True, index=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    keys = relationship("TenantKey", back_populates="tenant")
    settings = relationship("TenantSetting", back_populates="tenant", uselist=False)
    users = relationship("User", back_populates="tenant")

class TenantKey(Base):
    __tablename__ = "tenant_keys"
    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(String, ForeignKey("tenants.id"))
    api_key_hash = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    tenant = relationship("Tenant", back_populates="keys")

class TenantSetting(Base):
    __tablename__ = "tenant_settings"
    tenant_id = Column(String, ForeignKey("tenants.id"), primary_key=True)
    daily_limit = Column(Integer, default=10)
    allowed_assets = Column(String, default="XAUUSD,EURUSD,AUDCAD,BTCUSD,ETHUSD")
    branding_json = Column(Text)
    
    tenant = relationship("Tenant", back_populates="settings")

class AdminUser(Base):
    __tablename__ = "admin_users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    role = Column(String, default="SUPPORT") # OWNER, ADMIN, SUPPORT
    is_active = Column(Boolean, default=True)

class User(Base):
    __tablename__ = "users"
    id = Column(String, primary_key=True, index=True) # Could be Clerk ID
    tenant_id = Column(String, ForeignKey("tenants.id"))
    email = Column(String, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    tenant = relationship("Tenant", back_populates="users")
    consents = relationship("Consent", back_populates="user")
    usage = relationship("TenantUsageDaily", back_populates="user")
    subscription = relationship("Subscription", back_populates="user", uselist=False)

class Consent(Base):
    __tablename__ = "consents"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.id"))
    status = Column(String) # ACTIVE, PENDING
    accepted_at = Column(DateTime(timezone=True), server_default=func.now())
    version = Column(String)
    
    user = relationship("User", back_populates="consents")

class AnalysisSnapshot(Base):
    __tablename__ = "analysis_snapshots"
    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(String, index=True)
    user_id = Column(String, index=True)
    symbol = Column(String, index=True)
    timeframe = Column(String)
    output_json = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class TenantUsageDaily(Base):
    __tablename__ = "tenant_usage_daily"
    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(String, index=True)
    user_id = Column(String, ForeignKey("users.id"))
    date = Column(String, index=True) # YYYY-MM-DD
    analyses_count = Column(Integer, default=0)
    
    user = relationship("User", back_populates="usage")

class AuditLog(Base):
    __tablename__ = "audit_log"
    id = Column(Integer, primary_key=True, index=True)
    admin_id = Column(Integer, nullable=True)
    tenant_id = Column(String, nullable=True)
    action = Column(String)
    details = Column(Text)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())

# Payment & Subscription Models
class PlanType(str, enum.Enum):
    LITE = "LITE"
    PRO_MONTHLY = "PRO_MONTHLY"
    PRO_YEARLY = "PRO_YEARLY"

class SubStatus(str, enum.Enum):
    PENDING = "PENDING"
    ACTIVE = "ACTIVE"
    EXPIRED = "EXPIRED"

class Subscription(Base):
    __tablename__ = "subscriptions"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.id"), unique=True)
    plan = Column(String, default=PlanType.LITE)
    status = Column(String, default=SubStatus.PENDING)
    current_period_start = Column(DateTime(timezone=True), nullable=True)
    current_period_end = Column(DateTime(timezone=True), nullable=True)
    renewals_count = Column(Integer, default=0)
    
    user = relationship("User", back_populates="subscription")
    payments = relationship("Payment", back_populates="subscription")

class PaymentType(str, enum.Enum):
    INITIAL = "INITIAL"
    RENEWAL = "RENEWAL"
    REACTIVATION = "REACTIVATION"

class Payment(Base):
    __tablename__ = "payments"
    id = Column(Integer, primary_key=True, index=True)
    subscription_id = Column(Integer, ForeignKey("subscriptions.id"))
    method = Column(String) # IBAN, USDT, STRIPE
    amount = Column(Float)
    currency = Column(String, default="EUR")
    tx_reference = Column(String, nullable=True)
    status = Column(String, default="PENDING") # PENDING, VERIFIED, REJECTED
    payment_type = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    subscription = relationship("Subscription", back_populates="payments")

# Affiliate Models
class Affiliate(Base):
    __tablename__ = "affiliates"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.id"), unique=True)
    ref_code = Column(String, unique=True, index=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Referral(Base):
    __tablename__ = "referrals"
    id = Column(Integer, primary_key=True, index=True)
    affiliate_id = Column(Integer, ForeignKey("affiliates.id"))
    referred_user_id = Column(String, ForeignKey("users.id"), unique=True) # First touch attribution
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Commission(Base):
    __tablename__ = "commissions"
    id = Column(Integer, primary_key=True, index=True)
    affiliate_id = Column(Integer, ForeignKey("affiliates.id"))
    payment_id = Column(Integer, ForeignKey("payments.id"))
    amount = Column(Float)
    commission_type = Column(String) # INITIAL, RENEWAL, REACTIVATION
    status = Column(String, default="PENDING") # PENDING, APPROVABLE, PAID
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Payout(Base):
    __tablename__ = "payouts"
    id = Column(Integer, primary_key=True, index=True)
    affiliate_id = Column(Integer, ForeignKey("affiliates.id"))
    amount = Column(Float)
    status = Column(String, default="PENDING") # PENDING, PAID
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class AffiliateSetting(Base):
    __tablename__ = "affiliate_settings"
    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(String, ForeignKey("tenants.id"), unique=True)
    rate_initial_monthly = Column(Float, default=0.20)
    rate_initial_yearly = Column(Float, default=0.20)
    rate_renewal_monthly = Column(Float, default=0.10)
    rate_renewal_yearly = Column(Float, default=0.10)
    rate_reactivation_monthly = Column(Float, default=0.10)
    rate_reactivation_yearly = Column(Float, default=0.10)
    grace_days = Column(Integer, default=7)
    hold_days = Column(Integer, default=7)
    min_payout_amount = Column(Float, default=50.0)
