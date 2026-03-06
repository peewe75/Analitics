from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
import app.models as models
from app.dependencies import require_consent

router = APIRouter(prefix="", tags=["analyze"])

@router.get("/assets")
def get_assets():
    """ Step 5 - Asset Registry Lite (immutable) """
    return {
        "allowed_assets": ["XAUUSD", "EURUSD", "AUDCAD", "BTCUSD", "ETHUSD"]
    }

from app.engine import technical, scoring, scenarios, output, pro_analysis, ai_engine

@router.post("/analyze")
def analyze_asset(
    payload: dict,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_consent)
):
    """ Post an analysis request. Guarded by require_consent """
    symbol = payload.get("symbol")
    if symbol not in ["XAUUSD", "EURUSD", "AUDCAD", "BTCUSD", "ETHUSD"]:
        raise HTTPException(status_code=400, detail="SYMBOL_NOT_ALLOWED")
        
    # Check subscription status
    is_pro = False
    if current_user.subscription and current_user.subscription.status == models.SubStatus.ACTIVE:
        if current_user.subscription.plan in [models.PlanType.PRO_MONTHLY, models.PlanType.PRO_YEARLY]:
            is_pro = True

    # Mock data aggregation
    bucket_data = {
        "H1": {"close": [1.10, 1.11], "high": [1.12], "low": [1.09]},
        "H4": {"close": [1.10, 1.11], "high": [1.12], "low": [1.09], "volume": [1000, 2000]},
        "D1": {"close": [1.10, 1.11], "high": [1.12], "low": [1.09]}
    }
    macro_data = {"is_event_today": False}
    data_quality = {"is_low_confidence": False}

    # Core Technical (LITE + Foundation)
    tech = technical.analyze_technical(bucket_data)
    
    # Advanced Technical (PRO ONLY)
    pro_data = {}
    if is_pro:
        pro_data = pro_analysis.analyze_pro_features(bucket_data)
    
    # Scoring
    score = scoring.run_scoring(tech, macro_data, data_quality)
    
    # Scenarios
    scens = scenarios.generate_scenarios(tech["regime"], score["context_score"], tech["timeframe_bias"])
    
    # AI Narrative (PRO ONLY)
    narrative = ""
    if is_pro:
        analysis_context = {
            "technical": tech,
            "pro": pro_data,
            "score": score
        }
        narrative = ai_engine.generate_pro_narrative(analysis_context)
    
    # Composer
    final_output = output.compose_output(
        tenant_id=current_user.tenant_id,
        symbol=symbol,
        technical_data=tech,
        scoring_data=score,
        scenarios=scens,
        pro_data=pro_data if is_pro else None,
        narrative=narrative if is_pro else None
    )
    
    return final_output

@router.get("/analysis/latest")
def get_latest_analysis(
    current_user: models.User = Depends(require_consent),
    db: Session = Depends(get_db)
):
    """ Mock history retrieval """
    return []

@router.get("/analysis/history")
def get_history(
    current_user: models.User = Depends(require_consent),
    db: Session = Depends(get_db)
):
    """ Mock history retrieval """
    return []
