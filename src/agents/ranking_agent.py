import json
import logging
import re
from datetime import datetime
from typing import List, Dict
from src.llm_router import llm_router
from src.memory.source_cache import source_cache

logger = logging.getLogger(__name__)

def rank_and_filter(raw_news: List[Dict], max_results: int = 18) -> List[Dict]:
    # Removes exact duplicates
    unique_news = list({n["id"]: n for n in raw_news if "id" in n}.values())
    
    logger.info(f"Total news to evaluate: {len(unique_news)}. Starting rapid chunk filtering...")
    
    if len(unique_news) <= max_results:
        return unique_news

    chunk_size = 35
    selected_from_chunks = []
    today_date = datetime.now().strftime('%d/%m/%Y')
    
    for i in range(0, len(unique_news), chunk_size):
        chunk = unique_news[i:i+chunk_size]
        
        news_text = ""
        for n in chunk:
            desc = n.get("description", n.get("summary", ""))
            news_text += f"ID: {n['id']}\nTITLE: {n.get('title', '')}\nSOURCE: {n.get('source', '')}\nDESCRIPTION: {desc}\n\n"

        system_prompt = f"""You are J.A.R.V.I.S.'s Chief Analyst.
TODAY's DATE: {today_date}. Use this date as an absolute reference to assess event freshness.

You will receive a block of news. SELECT THE 7 MOST IMPORTANT ITEMS (global impact, finance, innovation).

RULE 1 (ANTI-ZOMBIE FILTER): If an event logically belongs to the past, COMPLETELY IGNORE IT.
RULE 2: If an academic paper (e.g., ArXiv) is present, you MUST include at least one. NEVER omit major stock market crashes.

Return EXCLUSIVELY a JSON array in this exact format:
[
    {{"id": "id_1", "area": "FINANCE"}},
    {{"id": "id_2", "area": "RESEARCH"}}
]

ATTENTION: If you decide that ALL news in this block is irrelevant or old, you must return an empty JSON array: []
Absolutely NO explanatory words. Only the JSON array.
"""

        try:
            logger.info(f"Ranking chunk {i//chunk_size + 1}/{len(unique_news)//chunk_size + 1}...")
            response = llm_router.invoke(prompt=news_text, system_prompt=system_prompt)
            
            match = re.search(r'\[.*\]', response, re.DOTALL)
            if not match:
                raise ValueError("No JSON array found in response.")
                
            json_str = match.group(0)
            winners = json.loads(json_str)
            
            for w in winners:
                original_news = next((item for item in chunk if item["id"] == w.get("id")), None)
                if original_news:
                    original_news["area"] = w.get("area", "MIX")
                    selected_from_chunks.append(original_news)
                
        except Exception as e:
            logger.warning(f"Skipping chunk due to JSON error: {e}")

    # Perfect Balancing
    final_selection = []
    counts = {"GEOPOLITICA": 0, "FINANCE": 0, "TECH": 0, "RESEARCH": 0}
    
    # Priority 1: At least 1 or 2 Research Papers
    for n in selected_from_chunks:
        area = n.get("area", "MIX").upper()
        if area == "RESEARCH" and counts["RESEARCH"] < 2:
            final_selection.append(n)
            counts["RESEARCH"] += 1
            
    # Priority 2: Everything else with wider limits for Finance
    for n in selected_from_chunks:
        if len(final_selection) >= max_results: break
        if n in final_selection: continue 
        
        area = n.get("area", "MIX").upper()
        if area == "FINANCE" and counts["FINANCE"] < 6:
            final_selection.append(n)
            counts["FINANCE"] += 1
        elif area in counts and counts[area] < 5:
            final_selection.append(n)
            counts[area] += 1
        elif len(final_selection) < max_results:
             final_selection.append(n)
             
    logger.info(f"Top {len(final_selection)} extracted (Geo: {counts.get('GEOPOLITICA',0)}, Fin: {counts.get('FINANCE',0)}, Tech: {counts.get('TECH',0)}, Research: {counts.get('RESEARCH',0)}).")
    
    logger.info("Starting Caching of full texts and LaTeX for selected news...")
    for n in final_selection:
        source_cache.fetch_and_cache(n)
        
    return final_selection