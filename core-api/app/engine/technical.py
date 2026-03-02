from typing import List, Dict, Any

def calculate_ema(prices: List[float], period: int = 200) -> float:
    """ Mock EMA calculation """
    if not prices:
        return 0.0
    return sum(prices[-period:]) / min(len(prices), period)

def calculate_rsi(prices: List[float], period: int = 14) -> float:
    """ Mock RSI calculation """
    return 50.0  # neutral

def calculate_atr(highs: List[float], lows: List[float], closes: List[float], period: int = 14) -> float:
    """ Mock ATR calculation """
    return 1.5

def determine_bias(current_price: float, ema200: float, rsi: float) -> str:
    """
    Bias per TF (neutral zone 0.15% + RSI confirm)
    Returns: BULLISH, BEARISH, NEUTRAL
    """
    if current_price == 0 or ema200 == 0:
        return "NEUTRAL"
        
    diff_pct = abs(current_price - ema200) / ema200
    
    if diff_pct < 0.0015:
        return "NEUTRAL"
        
    if current_price > ema200 and rsi > 50:
        return "BULLISH"
    elif current_price < ema200 and rsi < 50:
        return "BEARISH"
        
    return "NEUTRAL"

def determine_regime(tf_biases: Dict[str, str]) -> str:
    """ Regime TREND/RANGE based on multiple timeframes """
    bullish_count = sum(1 for b in tf_biases.values() if b == "BULLISH")
    bearish_count = sum(1 for b in tf_biases.values() if b == "BEARISH")
    
    if bullish_count >= 2 or bearish_count >= 2:
        return "TREND"
    return "RANGE"

def calculate_zones_fractal(highs: List[float], lows: List[float], atr: float) -> List[Dict[str, float]]:
    """ Zones S/R via fractal 5L/5R su H4 + buffer ATR """
    # Mocking zone calculation returning ranges (lower/upper) rule
    return [
        {"type": "RESISTANCE", "lower": 1.1000, "upper": 1.1000 + (atr * 0.5)},
        {"type": "SUPPORT", "lower": 1.0500 - (atr * 0.5), "upper": 1.0500}
    ]

def analyze_technical(data_buckets: Dict[str, Any]) -> Dict[str, Any]:
    """ 
    Main entry point for step 8 technical engine 
    data_buckets: dict of standard TF data (H1, H4, D1, etc)
    """
    tf_biases = {}
    key_zones = []
    
    # Process each timeframe
    for tf, data in data_buckets.items():
        closes = data.get("close", [])
        if not closes:
            tf_biases[tf] = "NEUTRAL"
            continue
            
        current_price = closes[-1]
        ema200 = calculate_ema(closes, 200)
        rsi14 = calculate_rsi(closes, 14)
        
        bias = determine_bias(current_price, ema200, rsi14)
        tf_biases[tf] = bias
        
        # Calculate zones on H4
        if tf == "H4":
            atr = calculate_atr(data.get("high", []), data.get("low", []), closes, 14)
            key_zones = calculate_zones_fractal(data.get("high", []), data.get("low", []), atr)
            
    regime = determine_regime(tf_biases)
    
    return {
        "timeframe_bias": tf_biases,
        "regime": regime,
        "key_zones": key_zones
    }
