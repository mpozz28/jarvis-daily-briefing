import logging
import json
import re
import uuid
from typing import List, Dict
from src.llm_router import llm_router

logger = logging.getLogger(__name__)

def connect_the_dots(ranked_news: List[Dict]) -> List[Dict]:
    logger.info("Starting Multi-Document Reasoning (Knowledge Graph Generation)...")
    
    # Abbiamo bisogno di almeno 2 articoli per fare una correlazione trasversale
    if len(ranked_news) < 2:
        logger.warning("Not enough articles to generate cross-document insights.")
        return []
        
    # Limitiamo il contesto ai top 15 per evitare allucinazioni e risparmiare token
    top_news = ranked_news[:15]
    
    valid_ids = set()
    news_context = "SELECTED NEWS LIST:\n"
    for idx, n in enumerate(top_news):
        news_id = str(n.get('id', ''))
        valid_ids.add(news_id)  # Salviamo gli ID reali per la validazione successiva
        desc = n.get('description', n.get('summary', ''))
        news_context += f"NEWS_ID: {news_id} | [{n.get('area', 'MIX')}] {n.get('title', '')}\nSUMMARY: {desc}\n\n"

    system_prompt = """You are J.A.R.V.I.S.'s Lead Intelligence Analyst.
    Your task is to perform Multi-Document Reasoning. You must find non-obvious correlations between DIFFERENT news articles provided in the context.
    Do NOT just summarize single articles. You MUST connect at least TWO distinct articles that share a hidden macro-trend (e.g., a geopolitical event affecting a tech market, or an AI paper solving a finance problem).
    
    Generate up to 3 brilliant insights.
    
    You MUST output ONLY a valid JSON array of objects. Do not use markdown blocks (no ```json).
    Strict Schema Required:
    [
      {
        "insight_id": "unique_string",
        "item_ids": ["id_from_article_1", "id_from_article_2"],
        "hypothesis": "One sharp, analytical sentence explaining the correlation.",
        "domains": ["geopolitics", "tech"],
        "confidence": 0.85,
        "evidence": ["Exact quote or fact from article 1", "Exact quote or fact from article 2"]
      }
    ]"""

    try:
        response = llm_router.invoke(
            prompt=news_context, 
            system_prompt=system_prompt,
            preferred_model="openai/gpt-oss-120b" 
        )
        
        # Robust JSON extraction
        match = re.search(r'\[.*\]', response, re.DOTALL)
        if not match:
            clean_json = response.strip()
            if clean_json.startswith('```json'):
                clean_json = clean_json.removeprefix('```json').removesuffix('```').strip()
            elif clean_json.startswith('```'):
                clean_json = clean_json.removeprefix('```').removesuffix('```').strip()
        else:
            clean_json = match.group(0)
            
        raw_insights = json.loads(clean_json)
        
        # Validation Layer (Hallucination Defense)
        validated_insights = []
        for item in raw_insights:
            # Assicuriamoci che l'LLM non abbia allucinato (inventato) ID inesistenti
            connected_ids = [str(i) for i in item.get('item_ids', []) if str(i) in valid_ids]
            
            # Accettiamo solo vere correlazioni multiple (almeno 2 ID corretti)
            if len(connected_ids) >= 2:
                validated_insights.append({
                    "insight_id": item.get("insight_id", f"ins_{uuid.uuid4().hex[:6]}"),
                    "item_ids": connected_ids,
                    "hypothesis": item.get("hypothesis", "Unknown correlation."),
                    "domains": item.get("domains", []),
                    "confidence": float(item.get("confidence", 0.5)),
                    "evidence": item.get("evidence", [])
                })
        
        logger.info(f"Generated {len(validated_insights)} validated multi-document insights.")
        return validated_insights[:3]
        
    except Exception as e:
        logger.error(f"Error in Connect the Dots JSON parsing: {e}")
        
    return []