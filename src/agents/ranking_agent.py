import json
import logging

from src.agents.scoring_agent import score_and_filter_candidates
from src.llm_router import llm_router

logger = logging.getLogger(__name__)


def rank_and_filter(news_list: list, max_items: int = 15, reference_time=None) -> list:
    """
    Fase 1: Pre-filtraggio deterministico veloce (Python).
    Fase 2: Reranking semantico di precisione (LLM-as-a-Judge).
    """
    if not news_list:
        return []

    # --- FASE 1: DETERMINISTIC SCORING ---
    # Passiamo il reference_time per consentire l'evaluation riproducibile nel tempo
    top_candidates = score_and_filter_candidates(
        news_list, max_candidates=20, reference_time=reference_time
    )

    # --- FASE 2: LLM SEMANTIC RERANKING ---
    logger.info("Executing LLM Semantic Reranking on Top Candidates...")

    system_prompt = """You are an Enterprise AI Reranker.
You will receive a list of highly authoritative news articles.
Your job is to perform Semantic Reranking. Assign a 'semantic_score' (0-100) based on the macroeconomic or technological impact of the news.
You must output ONLY a valid JSON array of objects. Do not use markdown blocks.
Format required:
[
    {"id": "id_here", "semantic_score": 85},
    {"id": "another_id", "semantic_score": 12}
]"""

    prompt = "Evaluate the following pre-filtered articles:\n\n"
    for n in top_candidates:
        prompt += f"ID: {n.get('id')}\nTitle: {n.get('title')}\nSummary: {n.get('summary')}\nSource: {n.get('source')}\n\n"

    score_map = {}
    try:
        response = llm_router.invoke(
            prompt=prompt,
            system_prompt=system_prompt,
            preferred_model="openai/gpt-oss-120b",
        )

        clean_json = response.strip()
        if clean_json.startswith("```json"):
            clean_json = clean_json.removeprefix("```json").removesuffix("```").strip()
        elif clean_json.startswith("```"):
            clean_json = clean_json.removeprefix("```").removesuffix("```").strip()

        scores = json.loads(clean_json)
        for item in scores:
            score_map[str(item.get("id"))] = item.get("semantic_score", 0)

    except Exception as e:
        logger.error(
            f"LLM Reranking failed: {e}. Falling back to deterministic sorting."
        )

    # Aggiorniamo i punteggi finali
    for n in top_candidates:
        n["relevance_score"] = score_map.get(
            str(n.get("id")), n.get("deterministic_score", 0)
        )

    # Ultimo sorting definitivo
    ranked_news = sorted(
        top_candidates, key=lambda x: x.get("relevance_score", 0), reverse=True
    )

    if ranked_news:
        logger.info(
            f"Reranking completed. Top article: {ranked_news[0].get('title')} (Score: {ranked_news[0].get('relevance_score')})"
        )

    return ranked_news[:max_items]
