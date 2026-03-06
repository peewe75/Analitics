from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from app.database import get_db
from app.dependencies import get_current_user, get_current_admin
from app.services import payments
from typing import Dict, Any
import app.models as models

router = APIRouter(prefix="/payments", tags=["payments"])

@router.post("/submit")
def submit_payment_proof(
    payload: Dict[str, Any] = Body(...), # method, amount, tx_reference
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user) # Normal user accessing
):
    """ Submit a manual payment proof (Crypto/Bank Transfer) """
    method = payload.get("method")
    amount = payload.get("amount")
    tx_reference = payload.get("tx_reference")
    
    if not all([method, amount, tx_reference]):
        raise HTTPException(status_code=400, detail="Missing payment details")
        
    try:
        payment = payments.submit_payment(db, user.id, method, float(amount), tx_reference)
        return {"status": "success", "message": "Payment submitted for review", "payment_id": payment.id}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/{payment_id}/verify")
def verify_manual_payment(
    payment_id: str,
    db: Session = Depends(get_db),
    admin_user: models.AdminUser = Depends(get_current_admin)
):
    """ [ADMIN ONLY] Verify a manual payment and activate the subscription. """
    try:
        payment = payments.verify_payment(db, payment_id, admin_user.id)
        return {"status": "success", "message": "Payment verified and subscription activated"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/{payment_id}/reject")
def reject_manual_payment(
    payment_id: str,
    payload: Dict[str, str], # reason
    db: Session = Depends(get_db),
    admin_user: models.AdminUser = Depends(get_current_admin)
):
    """ [ADMIN ONLY] Reject a manual payment. """
    reason = payload.get("reason", "No reason provided")
    try:
        payments.reject_payment(db, payment_id, admin_user.id, reason)
        return {"status": "success", "message": "Payment rejected"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
