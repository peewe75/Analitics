from fastapi import Depends, HTTPException, status, Header, Request
from sqlalchemy.orm import Session
from app.database import get_db
import app.models as models
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

def get_current_user(
    authorization: str = Header(None),
    db: Session = Depends(get_db)
) -> models.User:
    """ Validates Clerk JWT or custom auth """
    if not authorization:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    # TODO: Verify Clerk Token
    
    # Placeholder mock user retrieval
    user = db.query(models.User).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
        
    return user

def require_consent(current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
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
