import json
from typing import Dict, Any
from fastapi import HTTPException

# Constants for Step 12
FORBIDDEN_WORDS = [
    "buy", "sell", "compra", "vendi", "entra", "esci", 
    "target", "take profit", "stop loss", "segnale", 
    "garantito", "profitto", "rendimento"
]

def sanitize_forbidden_words(text: str) -> bool:
    """ Returns True if text contains forbidden words """
    lower_text = text.lower()
    for word in FORBIDDEN_WORDS:
        if word in lower_text:
            return True
    return False

def validate_output_schema(output_data: Dict[str, Any]) -> None:
    """ Basic sanity checking for Step 12 Validation Gates """
    required_fields = [
        "schema_version", "engine_version", "tenant_id", "symbol", 
        "generated_at", "market_context", "technical_structure", 
        "scenarios", "run_id"
    ]
    
    for field in required_fields:
        if field not in output_data:
            raise HTTPException(status_code=500, detail="VALIDATION_FAILED: Missing fields")

    # Check scenarios for forbidden words deeply
    for scenario in output_data.get("scenarios", []):
        for val in scenario.values():
            if isinstance(val, str) and sanitize_forbidden_words(val):
                raise HTTPException(status_code=500, detail="VALIDATION_FAILED: Forbidden word detected")
                
def compose_output(
    tenant_id: str,
    symbol: str, 
    technical_data: Dict[str, Any], 
    scoring_data: Dict[str, Any], 
    scenarios: list,
    macro_context: str = "",
    pro_data: Dict[str, Any] = None,
    narrative: str = None
) -> Dict[str, Any]:
    """ Assembles final dictionary complying to schema v1.0 """
    
    is_pro = pro_data is not None

    output = {
        "schema_version": "1.0",
        "engine_version": "1.0.0",
        "tenant_id": tenant_id,
        "symbol": symbol,
        "run_id": "mock_run_12345", 
        "generated_at": "2026-03-02T12:00:00Z", 
        "data_sources": ["alpha_vantage", "binance"], 
        "market_context": {
            "regime": technical_data.get("regime", "RANGE"),
            "context_score": scoring_data.get("context_score", 50),
            "flags": scoring_data.get("flags", [])
        },
        "technical_structure": {
            "timeframe_bias": technical_data.get("timeframe_bias", {}),
            "key_zones": technical_data.get("key_zones", [])
        },
        "scenarios": scenarios,
        "macro_context": macro_context,
        "premium_features": pro_data if is_pro else {},
        "ai_narrative": narrative if is_pro else "Funzionalità disponibile solo per utenti PRO.",
        "news_digest": "Notiziario statico (LITE)",
        "risk_notes": "Il trading comporta rischi. (LITE)" if not is_pro else "Analisi avanzata. Opera con cautela.",
        "disclaimer": "L'analisi è fornita a solo scopo educativo, softi non è un consulente finanziario."
    }
    
    validate_output_schema(output)
    
    return output
