from src.llm_router import llm_router
from src.utils.observability import logger


def write_jarvis_briefing(
    ranked_news: list, insights: list, market_metrics: dict = None
) -> str:
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
    Your task is to write a comprehensive, in-depth morning executive briefing for your creator.
    
    GUIDELINES:
    1. Start with a sophisticated greeting (addressing the user as 'Sir').
    2. Write a rich, multi-paragraph narrative (at least 4 to 5 paragraphs). Take your time to elaborate on the implications of the news.
    3. Group the topics logically (e.g., dedicate one paragraph to Geopolitics/Macro, and another to Tech/AI breakthroughs).
    4. ACADEMIC PAPERS: If any scientific papers, research, or ArXiv preprints are present in the news, you MUST explicitly highlight them and explain their technical relevance and potential real-world impact.
    5. EXPLICITLY expand on the 'SYSTEM CORRELATIONS'. Explain to the user how these different events might be connected.
    6. If 'DETERMINISTIC MARKET METRICS' are provided, dedicate a specific paragraph to a sharp financial update. YOU MUST USE THE EXACT NUMBERS PROVIDED.
    7. Do NOT use markdown (no **, no ##, no bullet points). Write purely conversational prose that sounds perfect when read aloud by a Text-to-Speech engine.
    8. End with a sharp, motivational closing statement.
    """

    prompt = "--- TOP NEWS TODAY ---\n"
    for idx, n in enumerate(ranked_news[:8]):
        prompt += f"{idx + 1}. {n.get('title')} - {n.get('summary')}\n"

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
            preferred_model="openai/gpt-oss-120b",
        )
        # Pulizia caratteri che potrebbero inceppare la voce
        clean_narrative = narrative.replace("*", "").replace("#", "").strip()
        logger.info(
            "Narrative generation completed.", extra={"component": "writer_agent"}
        )
        return clean_narrative
    except Exception as e:
        logger.error(f"Error generating narrative: {e}", exc_info=True)
        return "Good morning, Sir. I am currently experiencing an anomaly in my linguistic processing unit. The raw data is available below."
