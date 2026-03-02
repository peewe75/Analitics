from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from app.database import get_db
from app.dependencies import get_current_user
from app.services import affiliates
from app.models import Affiliate, Referral, Commission
from typing import Dict, Any

router = APIRouter(prefix="/api/v1/affiliates", tags=["affiliates"])

@router.post("/join")
def join_affiliate_program(
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    """ Become an affiliate and generate a ref code. """
    affiliate = affiliates.create_affiliate(db, user["user_id"])
    return {
        "status": "success", 
        "data": {
            "ref_code": affiliate.ref_code
        }
    }

@router.get("/dashboard")
def get_affiliate_dashboard(
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    """ View affiliate stats, referrals, and pending commissions. """
    affiliate = db.query(Affiliate).filter(Affiliate.user_id == user["user_id"]).first()
    if not affiliate:
        raise HTTPException(status_code=404, detail="Not an affiliate yet.")
        
    # Get stats
    total_referrals = db.query(Referral).filter(Referral.affiliate_id == affiliate.id).count()
    
    # Needs optimization in prod, just basic sum for now
    commissions = db.query(Commission).filter(Commission.affiliate_id == affiliate.id).all()
    total_earned = sum(c.amount for c in commissions if c.status == "PAID")
    total_pending = sum(c.amount for c in commissions if c.status in ["PENDING", "APPROVABLE"])
    
    return {
        "status": "success",
        "data": {
            "ref_code": affiliate.ref_code,
            "total_referrals": total_referrals,
            "total_earned": total_earned,
            "total_pending": total_pending
        }
    }
