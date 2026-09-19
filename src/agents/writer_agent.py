import logging
import json
from src.llm_router import llm_router
from src.utils.observability import logger

def write_jarvis_briefing(ranked_news: list, insights: list, market_metrics: dict = None) -> str:
    """
    Generates the narrative voice of J.A.R.V.I.S. using news, insights, and deterministic quantitative data.
    """
    logger.info("Generating narrative briefing...")
    
    if not ranked_news:
        return "Good morning, Sir. I have scanned the global networks, but it appears there are no significant events to report today."

    # Formattiamo i dati quantitativi in modo leggibile
    market_text = ""
    if market_metrics:
        market_text = "\n--- DETERMINISTIC MARKET METRICS (DO NOT CALCULATE, JUST READ THESE EXACT NUMBERS) ---\n"
        for ticker, data in market_metrics.items():
            market_text += f"{data['name']}: {data['latest_price_usd']}$ | Daily Return: {data['daily_return_pct']}% | Volatility: {data['annualized_volatility_pct']}% | Trend: {data['market_regime']}\n"
    
    system_prompt = """You are J.A.R.V.I.S., the highly advanced, ironic, and brilliant AI assistant (British tone).
    Your task is to write the morning executive briefing for your creator.
    
    GUIDELINES:
    1. Start with a sophisticated, brief greeting (addressing the user as 'Sir').
    2. Seamlessly weave the top news and insights into a cohesive 2-3 paragraph narrative.
    3. If 'DETERMINISTIC MARKET METRICS' are provided, include a brief, sharp financial update. YOU MUST USE THE EXACT NUMBERS PROVIDED. Do not hallucinate or round them improperly.
    4. Do NOT use markdown (no **, no ##, no bullet points). Write purely conversational prose that sounds perfect when read aloud by a Text-to-Speech engine.
    5. End with a sharp, motivational closing statement.
    """
    
    prompt = "--- TOP NEWS TODAY ---\n"
    for idx, n in enumerate(ranked_news[:5]):
        prompt += f"{idx+1}. {n.get('title')} - {n.get('summary')}\n"
        
    if insights:
        prompt += "\n--- SYSTEM CORRELATIONS (Connect the dots) ---\n"
        for i in insights:
            prompt += f"- {i.get('hypothesis')}\n"
            
    if market_text:
        prompt += market_text
        
    try:
        narrative = llm_router.invoke(
            prompt=prompt,
            system_prompt=system_prompt,
            preferred_model="openai/gpt-oss-120b"
        )
        # Pulizia caratteri che potrebbero inceppare la voce
        clean_narrative = narrative.replace('*', '').replace('#', '').strip()
        logger.info("Narrative generation completed.", extra={"component": "writer_agent"})
        return clean_narrative
    except Exception as e:
        logger.error(f"Error generating narrative: {e}", exc_info=True)
        return "Good morning, Sir. I am currently experiencing an anomaly in my linguistic processing unit. The raw data is available below."