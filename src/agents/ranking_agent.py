import json
import logging
import time
from src.llm_router import llm_router

logger = logging.getLogger(__name__)

def rank_and_filter(news_list: list, max_items: int = 15) -> list:
    """
    Valuta e ordina le notizie usando il pattern LLM-as-a-Judge.
    Implementa Batch Processing per evitare la troncatura del JSON e i Rate Limits.
    """
    if not news_list:
        return []

    logger.info(f"Total news to evaluate: {len(news_list)}. Using LLM-as-a-Judge (Batch Processing)...")

    system_prompt = """You are J.A.R.V.I.S., a master intelligence analyst.
You must output ONLY a valid JSON array of objects. Do not use markdown blocks (```json), do not write any text outside the JSON.
Format required:
[
    {"id": "id_here", "importance_score": 85},
    {"id": "another_id", "importance_score": 12}
]"""

    score_map = {}
    chunk_size = 20  # Elaboriamo 20 notizie alla volta per non saturare i token in output

    for i in range(0, len(news_list), chunk_size):
        chunk = news_list[i:i + chunk_size]
        
        prompt = "Evaluate the following news articles. Assign an 'importance_score' from 0 to 100 for each.\n"
        prompt += "Criteria: \n"
        prompt += "- 90-100: Global macroeconomic shift, AGI breakthrough, major geopolitical crisis.\n"
        prompt += "- 50-89: Important tech/finance news, significant corporate moves.\n"
        prompt += "- 0-49: Local news, gossip, minor updates, irrelevant.\n\n"
        
        for n in chunk:
            prompt += f"ID: {n.get('id')}\nTitle: {n.get('title')}\nSummary: {n.get('summary')}\nSource: {n.get('source')}\n\n"

        try:
            response = llm_router.invoke(
                prompt=prompt,
                system_prompt=system_prompt,
                preferred_model="openai/gpt-oss-120b" 
            )
            
            clean_json = response.strip()
            if clean_json.startswith('```json'):
                clean_json = clean_json.removeprefix('```json').removesuffix('```').strip()
            elif clean_json.startswith('```'):
                clean_json = clean_json.removeprefix('```').removesuffix('```').strip()
                
            scores = json.loads(clean_json)
            for item in scores:
                score_map[str(item.get('id'))] = item.get('importance_score', 0)
                
        except json.JSONDecodeError as e:
            logger.error(f"Ranking chunk {i//chunk_size + 1} failed (JSON error): {e}")
        except Exception as e:
            logger.error(f"Ranking chunk {i//chunk_size + 1} failed: {e}")
        
        # Pausa tattica per aggirare i Rate Limits rigorosi del Free Tier
        time.sleep(2.5)

    # Iniettiamo i punteggi (se una notizia ha fallito, prende 0 di default)
    for n in news_list:
        n['relevance_score'] = score_map.get(str(n.get('id')), 0)
        
    # Sorting deterministico in Python
    ranked_news = sorted(news_list, key=lambda x: x.get('relevance_score', 0), reverse=True)
    
    if ranked_news:
        logger.info(f"Scoring completed. Top article score: {ranked_news[0].get('relevance_score')} - {ranked_news[0].get('title')}")
    
    return ranked_news[:max_items]