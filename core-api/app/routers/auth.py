from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
import app.models as models
from app.dependencies import get_current_user
from pydantic import BaseModel
from typing import Optional

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/register")
def register(user_data: dict, db: Session = Depends(get_db)):
    """ Placeholder for clerk/local registration """
    return {"message": "User registered successfully"}

@router.post("/login")
def login(login_data: dict, db: Session = Depends(get_db)):
    """ Placeholder for login yielding JWT """
    return {"access_token": "mock_token", "token_type": "bearer"}

@router.get("/me")
async def read_users_me(current_user: models.User = Depends(get_current_user)):
    return {"id": current_user.id, "email": current_user.email}

consent_router = APIRouter(prefix="/consent", tags=["consent"])

class ConsentRequest(BaseModel):
    version: str = "1.0"

@consent_router.get("/status")
async def get_consent_status(current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    consent = db.query(models.Consent).filter(
        models.Consent.user_id == current_user.id,
        models.Consent.status == "ACTIVE"
    ).first()
    return {"has_consent": consent is not None}

@consent_router.post("/acknowledge")
async def acknowledge_consent(payload: ConsentRequest, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    # Check if consent already exists
    existing = db.query(models.Consent).filter(
        models.Consent.user_id == current_user.id,
        models.Consent.status == "ACTIVE"
    ).first()
    if existing:
        return {"message": "Consent already acknowledged", "consent_id": existing.id}
    
    consent = models.Consent(
        user_id=current_user.id,
        status="ACTIVE",
        version=payload.version
    )
    db.add(consent)
    db.commit()
    db.refresh(consent)
    return {"message": "Consent acknowledged", "consent_id": consent.id}
