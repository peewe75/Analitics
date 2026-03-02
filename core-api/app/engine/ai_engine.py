import os
import json
from typing import Dict, Any

# Mocking OpenAI response for now. In production, 'openai' library would be used.
# from openai import OpenAI
# client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def generate_pro_narrative(analysis_data: Dict[str, Any]) -> str:
    """
    Transforms JSON analysis into a premium narrative for PRO users.
    Ensures zero financial advice (mandatory requirement).
    """
    
    # Construct a detailed context for the AI
    # (In a real scenario, this would be a prompt sent to GPT-4o)
    
    bias_summary = analysis_data.get("technical", {}).get("timeframe_bias", {})
    regime = analysis_data.get("technical", {}).get("regime", "UNKNOWN")
    structure = analysis_data.get("pro", {}).get("market_structure", {}).get("last_event", "NEUTRAL")
    
    # BUILD PROMPT (Internal)
    prompt = f"""
    Act as a technical market analyst. Analyze the following data for the asset:
    - Multi-TF Biases: {bias_summary}
    - Regime: {regime}
    - Market Structure: {structure}
    
    Task: Write a 2-paragraph professional summary of the technical context.
    STRICT RULES:
    1. NEVER use words like 'BUY', 'SELL', 'INVEST', 'PROFIT', 'TARGET', 'STOP LOSS'.
    2. Focus ONLY on price action facts and technical structure.
    3. Maintain a neutral, descriptive tone.
    4. Language: EXCLUSIVELY ITALIAN.
    """
    
    # MOCK AI RESPONSE (Until user provides API Key)
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return (
            f"Il mercato si trova in una fase di {regime} con un bias prevalente {bias_summary.get('H4', 'NEUTRAL')}. "
            f"L'analisi della struttura ha rilevato un evento di {structure}, suggerendo una continuazione della dinamica corrente. "
            "Le zone di interesse volumetrico indicano una concentrazione di ordini non ancora mitigati che potrebbero influenzare la volatilità."
        )
    
    # Actual call would be here:
    # response = client.chat.completions.create(...)
    # return response.choices[0].message.content
    
    return "Analisi AI generata (Mock)."
