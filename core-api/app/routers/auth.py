from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
import app.models as models
from app.dependencies import get_current_user

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
def read_users_me(current_user: models.User = Depends(get_current_user)):
    return {"id": current_user.id, "email": current_user.email}

consent_router = APIRouter(prefix="/consent", tags=["consent"])

@consent_router.get("/status")
def get_consent_status(current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    consent = db.query(models.Consent).filter(
        models.Consent.user_id == current_user.id,
        models.Consent.status == "ACTIVE"
    ).first()
    return {"has_consent": consent is not None}

@consent_router.post("/acknowledge")
def acknowledge_consent(version: str, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    consent = models.Consent(
        user_id=current_user.id,
        status="ACTIVE",
        version=version
    )
    db.add(consent)
    db.commit()
    db.refresh(consent)
    return {"message": "Consent acknowledged", "consent_id": consent.id}
