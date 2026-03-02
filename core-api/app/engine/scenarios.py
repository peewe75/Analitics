from typing import Dict, Any, List

def generate_scenarios(regime: str, context_score: int, tf_bias: Dict[str, str]) -> List[Dict[str, str]]:
    """ 
    Sempre 2 scenari:
    - condition, interpretation, invalidation, risk_note
    No target, no TP/SL, no buy/sell. 
    """
    
    # Generic LITE static strings based on regime and bias logic
    primary_scenario = {
        "condition": "Se il prezzo mantiene il supporto critico",
        "interpretation": "Il quadro tecnico a breve termine indica una continuazione dell'attuale struttura",
        "invalidation": "Cedimento confermato al di sotto dell'area di supporto",
        "risk_note": "Possibile aumento di volatilit\u00e0 in concomitanza con eventi macroeconomici"
    }

    alternative_scenario = {
        "condition": "In caso di mancata tenuta dei livelli chiave",
        "interpretation": "Rotazione della struttura di mercato verso nuovi test dei livelli inferiori",
        "invalidation": "Recupero immediato e consolidamento sopra le zone di rigetto",
        "risk_note": "Aree soggette ad alta liquidit\u00e0 e test profondi"
    }
    
    # Simple deterministic tuning depending on trend vs range
    if regime == "TREND":
        primary_scenario["condition"] = "Se il mercato prosegue seguendo il momentum direzionale"
        alternative_scenario["condition"] = "Nel caso di esaurimento del momentum e deviazione strutturale"
        
    return [primary_scenario, alternative_scenario]
