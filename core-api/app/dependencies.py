from fastapi import Depends, HTTPException, status, Header, Request, Security
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.database import get_db
import app.models as models
from app.auth.clerk import get_clerk_user, security
import os

DEFAULT_TENANT_ID = os.getenv("DEFAULT_TENANT_ID", "softi")

def get_tenant(
    request: Request,
    x_tenant_id: str = Header(None, alias="X-TENANT-ID"),
    db: Session = Depends(get_db)
) -> models.Tenant:
    tenant_id = None
    
    # 1. Try X-TENANT-ID header
    if x_tenant_id:
        tenant_id = x_tenant_id
    
    # 2. Try subdomain
    if not tenant_id:
        host = request.headers.get("host", "")
        parts = host.split(".")
        if len(parts) >= 3 and parts[0] != "www": # assuming something like tenant.softianalyze.com
            subdomain = parts[0]
            tenant = db.query(models.Tenant).filter(models.Tenant.subdomain == subdomain).first()
            if tenant:
                tenant_id = tenant.id
    
    # 3. Fallback to default
    if not tenant_id:
        tenant_id = DEFAULT_TENANT_ID
        
    tenant = db.query(models.Tenant).filter(models.Tenant.id == tenant_id).first()
    if not tenant or not tenant.is_active:
        raise HTTPException(status_code=400, detail="Invalid or inactive tenant")
        
    return tenant

# Dummy API Key hash verifier for now
def verify_api_key(api_key: str, hashed_key: str) -> bool:
    # In reality use passlib to verify
    return True 

def get_tenant_by_api_key(
    x_api_key: str = Header(..., alias="X-API-KEY"),
    db: Session = Depends(get_db)
) -> models.Tenant:
    # Look up TenantKey by hash. 
    # For performance, we might cache this or store a prefix.
    # We will assume a naive approach for the MVP: iterate or store api keys with a known prefix
    # Proper specific implementation requires hashing matching.
    # Placeholder implementation:
    raise HTTPException(status_code=501, detail="API Key auth not fully implemented yet")

async def get_current_user(
    clerk_payload: dict = Depends(get_clerk_user),
    db: Session = Depends(get_db)
) -> models.User:
    """ Validates Clerk JWT and returns the user from DB """
    email = clerk_payload.get("email") or clerk_payload.get("emails", [None])[0] # Clerk payload varies
    clerk_id = clerk_payload.get("sub")
    
    if not clerk_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Clerk token")

    user = db.query(models.User).filter(models.User.id == clerk_id).first()
    if not user:
        # Auto-create user on first login from Clerk
        user = models.User(
            id=clerk_id,
            email=email or f"{clerk_id}@clerk.user",
            tenant_id=DEFAULT_TENANT_ID,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        
    return user

async def get_current_admin(
    clerk_payload: dict = Depends(get_clerk_user),
    db: Session = Depends(get_db)
) -> models.AdminUser:
    """ Validates Clerk JWT and checks if user is an admin by email """
    # Get email from Clerk payload. Clerk typically puts it in 'emails' or 'primary_email_address' 
    # but in a JWT it's often in a custom claim or 'email'
    email = clerk_payload.get("email")
    
    if not email:
        # Try finding email in different common Clerk claims
        email = clerk_payload.get("email_address")
        
    if not email:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Email not found in Clerk token")

    admin = db.query(models.AdminUser).filter(models.AdminUser.email == email, models.AdminUser.is_active == True).first()
    if not admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied: Not an administrator")
        
    return admin

async def require_consent(current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    consent = db.query(models.Consent).filter(
        models.Consent.user_id == current_user.id,
        models.Consent.status == "ACTIVE"
    ).first()
    
    if not consent:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="CONSENT_REQUIRED"
        )
    return current_user
