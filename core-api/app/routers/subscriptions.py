from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.dependencies import get_current_user, require_consent
from app.services import subscriptions
from typing import Dict, Any
import app.models as models

router = APIRouter(prefix="/api/v1/subscriptions", tags=["subscriptions"])

@router.get("/me")
def get_my_subscription(
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user)
):
    """ Get the current user's subscription status. """
    sub = subscriptions.get_subscription(db, user.id)
    return {
        "status": "success",
        "data": {
            "plan": sub.plan,
            "status": sub.status,
            "current_period_start": sub.current_period_start,
            "current_period_end": sub.current_period_end,
            "renewals_count": sub.renewals_count
        }
    }

@router.post("/request-pro")
def request_pro(
    payload: Dict[str, str], # {"plan_type": "PRO_MONTHLY|PRO_YEARLY"}
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user)
):
    """ Initiate a request to upgrade to a PRO plan. """
    plan_type = payload.get("plan_type")
    
    try:
        sub = subscriptions.request_pro_plan(db, user.id, plan_type)
        return {"status": "success", "message": f"Requested upgrade to {plan_type}", "subscription_id": sub.id}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
