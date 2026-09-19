import json
import logging
from src.llm_router import llm_router

logger = logging.getLogger(__name__)

def rank_and_filter(news_list: list, max_items: int = 15) -> list:
    """
    Valuta e ordina le notizie usando il pattern LLM-as-a-Judge.
    L'LLM assegna un punteggio semantico, Python ordina deterministicamente.
    """
    if not news_list:
        return []

    logger.info(f"Total news to evaluate: {len(news_list)}. Using LLM-as-a-Judge for scoring...")

    # 1. Prepariamo il prompt con i criteri di valutazione
    prompt = "Evaluate the following news articles. Assign an 'importance_score' from 0 to 100 for each.\n"
    prompt += "Criteria: \n"
    prompt += "- 90-100: Global macroeconomic shift, AGI breakthrough, major geopolitical crisis.\n"
    prompt += "- 50-89: Important tech/finance news, significant corporate moves.\n"
    prompt += "- 0-49: Local news, gossip, minor updates, irrelevant.\n\n"
    
    for n in news_list:
        # Passiamo solo ID, Titolo e Sommario per risparmiare token e latenza
        prompt += f"ID: {n.get('id')}\nTitle: {n.get('title')}\nSummary: {n.get('summary')}\nSource: {n.get('source')}\n\n"

    # 2. Forziamo l'output strutturato JSON (Data Contract)
    system_prompt = """You are J.A.R.V.I.S., a master intelligence analyst.
You must output ONLY a valid JSON array of objects. Do not use markdown blocks (```json), do not write any text outside the JSON.
Format required:
[
    {"id": "id_here", "importance_score": 85},
    {"id": "another_id", "importance_score": 12}
]"""

    try:
        # Chiamata al nostro router (che ora traccerà in automatico i token/costi!)
        response = llm_router.invoke(
            prompt=prompt,
            system_prompt=system_prompt,
            preferred_model="openai/gpt-oss-120b"  # Il 120b è ottimo per il reasoning
        )
        
        # 3. Pulizia e Parsing (Robusto contro le allucinazioni di formattazione)
        clean_json = response.strip()
        if clean_json.startswith('```json'):
            clean_json = clean_json.removeprefix('```json').removesuffix('```').strip()
        elif clean_json.startswith('```'):
            clean_json = clean_json.removeprefix('```').removesuffix('```').strip()
            
        scores = json.loads(clean_json)
        
        # 4. Mappiamo i punteggi (O(1) lookup)
        score_map = {str(item['id']): item.get('importance_score', 0) for item in scores}
        
        # 5. Iniettiamo i punteggi negli articoli originali
        for n in news_list:
            n['relevance_score'] = score_map.get(str(n.get('id')), 0)
            
        # 6. Sorting deterministico in Python (il modo giusto di farlo)
        ranked_news = sorted(news_list, key=lambda x: x.get('relevance_score', 0), reverse=True)
        
        logger.info(f"Scoring completed. Top article score: {ranked_news[0].get('relevance_score')} - {ranked_news[0].get('title')}")
        
        # Restituiamo solo le Top N notizie
        return ranked_news[:max_items]

    except json.JSONDecodeError as e:
        logger.error(f"Ranking failed: LLM did not return valid JSON. Error: {e}", exc_info=True)
        # Fallback Graceful: restituiamo la lista così com'è invece di far crashare l'app
        return news_list[:max_items]
    except Exception as e:
        logger.error(f"Critical error during ranking: {e}", exc_info=True)
        return news_list[:max_items]