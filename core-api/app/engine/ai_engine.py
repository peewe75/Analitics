import os
import json
import logging
from typing import Dict, Any

# Try to import the new google-genai sdk
try:
    from google import genai
    from google.genai import types
    has_genai = True
except ImportError:
    has_genai = False

logger = logging.getLogger(__name__)

def generate_pro_narrative(analysis_data: Dict[str, Any]) -> str:
    """
    Transforms JSON analysis into a premium narrative for PRO users.
    Ensures zero financial advice (mandatory requirement).
    Uses Gemini 2.0 Flash.
    """
    
    bias_summary = analysis_data.get("technical", {}).get("timeframe_bias", {})
    regime = analysis_data.get("technical", {}).get("regime", "UNKNOWN")
    structure = analysis_data.get("pro", {}).get("market_structure", {}).get("last_event", "NEUTRAL")
    
    # Fallback string
    fallback_response = (
        f"Il mercato si trova in una fase di {regime} con un bias prevalente {bias_summary.get('H4', 'NEUTRAL')}. "
        f"L'analisi della struttura ha rilevato un evento di {structure}, suggerendo una continuazione della dinamica corrente. "
        "Le zone di interesse volumetrico indicano una concentrazione di ordini non ancora mitigati che potrebbero influire sulla volatilità."
    )
    
    prompt = f"""
    Act as a technical market analyst. Analyze the following data for the asset:
    - Multi-TF Biases: {bias_summary}
    - Regime: {regime}
    - Market Structure: {structure}
    
    Task: Write a 2-paragraph professional summary of the technical context.
    STRICT RULES:
    1. NEVER use words like 'buy', 'sell', 'compra', 'vendi', 'invest', 'profit', 'target', 'stop loss'.
    2. Focus ONLY on price action facts and technical structure.
    3. Maintain a neutral, descriptive tone.
    4. Language: EXCLUSIVELY ITALIAN.
    """
    
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key or not has_genai:
        return fallback_response
    
    try:
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model='gemini-2.0-flash',
            contents=prompt,
        )
        if response.text:
            return response.text
        return fallback_response
    except Exception as e:
        logger.error(f"Error calling Gemini API: {e}")
        return fallback_response
