from typing import Dict, Any, List

def calculate_context_score(technical_data: Dict[str, Any], macro_data: Dict[str, Any]) -> int:
    """
    Context Score 0–100:
    - timeframe_alignment 0–40
    - ema_bias 0–20
    - rsi_condition 0–15
    - volatility 0–10
    - macro_flag 0–15
    """
    score = 0
    
    tf_bias = technical_data.get("timeframe_bias", {})
    bullish = sum(1 for b in tf_bias.values() if b == "BULLISH")
    bearish = sum(1 for b in tf_bias.values() if b == "BEARISH")
    
    # alignment (max 40)
    if bullish == 3 or bearish == 3:
        score += 40
    elif bullish == 2 or bearish == 2:
        score += 20
        
    # ema bias (max 20)
    score += 10 # Mock base 10
    
    # rsi condition (max 15)
    score += 10 # Mock base 10
    
    # volatility (max 10)
    score += 5 # Mock base 5
    
    # macro (max 15)
    if macro_data.get("is_event_today", False):
        score += 5
    else:
        score += 15
        
    # Cap at 100
    return min(100, score)

def determine_flags(technical_data: Dict[str, Any], macro_data: Dict[str, Any], data_quality: Dict[str, Any]) -> List[str]:
    """
    Flags: TF_CONFLICT, EVENT_WITHIN_3H, HIGH_VOLATILITY, LOW_DATA_CONFIDENCE, CRYPTO_LOW_AGG_CONFIDENCE
    """
    flags = []
    
    tf_bias = technical_data.get("timeframe_bias", {})
    bullish = sum(1 for b in tf_bias.values() if b == "BULLISH")
    bearish = sum(1 for b in tf_bias.values() if b == "BEARISH")
    
    if bullish > 0 and bearish > 0:
        flags.append("TF_CONFLICT")
        
    if macro_data.get("event_within_3h"):
        flags.append("EVENT_WITHIN_3H")
        
    if data_quality.get("is_low_confidence"):
        flags.append("LOW_DATA_CONFIDENCE")
        
    if data_quality.get("is_crypto_low_agg"):
        flags.append("CRYPTO_LOW_AGG_CONFIDENCE")
        
    return flags

def run_scoring(technical_data: Dict[str, Any], macro_data: Dict[str, Any], data_quality: Dict[str, Any]) -> Dict[str, Any]:
    """ Main entry point for step 9 scoring engine """
    
    score = calculate_context_score(technical_data, macro_data)
    flags = determine_flags(technical_data, macro_data, data_quality)
    
    return {
        "context_score": score,
        "flags": flags,
        "ai_refinement": 0 # Always 0 for Lite
    }
