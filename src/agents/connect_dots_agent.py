import logging
import json
import re
from typing import List, Dict
from src.llm_router import llm_router

logger = logging.getLogger(__name__)

def connect_the_dots(ranked_news: List[Dict]) -> List[Dict]:
    logger.info("Starting 'Connect the Dots' analysis (Structured Macro-Trend search)...")
    
    if not ranked_news:
        return []
        
    news_context = "SELECTED NEWS LIST:\n"
    for idx, n in enumerate(ranked_news):
        desc = n.get('description', n.get('summary', ''))
        news_context += f"NEWS_ID: {n['id']} | [{n.get('area', 'MIX')}] {n.get('title', '')} - {desc}\n\n"

    system_prompt = """You are J.A.R.V.I.S.'s Strategic Analyst.
    You receive a list of today's most important news (each has a NEWS_ID).
    You must extract 3 (THREE) brilliant and ironic Macro-Trends.
    
    1. The FIRST trend must cover Geopolitics, Global Security, or Society.
    2. The SECOND trend must cover exclusively Financial Markets. IF THERE ARE STOCK MARKET CRASHES OR FINANCIAL DATA IN THE LIST, MENTION THEM WITH THEIR EXACT NUMBERS.
    3. The THIRD trend MUST explain in a popular science manner an academic paper or a technological discovery present in the list.
    
    IMPORTANT: For each trend, identify the exact news item that inspired it and provide its ID.
    
    Return EXCLUSIVELY a JSON array in this exact format (with no other words):
    [
      {
        "target_id": "The ID of the primary news item that triggered the trend",
        "insight": "The text of the trend (written in British English, brilliant, accessible)"
      },
      ...
    ]
    """

    try:
        response = llm_router.invoke(
            prompt=news_context, 
            system_prompt=system_prompt,
            preferred_model="openai/gpt-oss-120b" 
        )
        
        match = re.search(r'\[.*\]', response, re.DOTALL)
        if match:
            insights_data = json.loads(match.group(0))
            logger.info(f"Found {len(insights_data)} macro-trends with perfect ID matching.")
            return insights_data
            
    except Exception as e:
        logger.error(f"Error in Connect the Dots JSON parsing: {e}")
        
    return []