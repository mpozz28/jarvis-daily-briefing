import logging
from datetime import datetime, timezone

import dateutil.parser

logger = logging.getLogger(__name__)

# Lookup table per la qualità delle fonti (Interpretabile e Configurabile)
SOURCE_QUALITY_WEIGHTS = {
    "arxiv": 1.0,  # Ricerca AI/ML ha priorità massima
    "reuters": 0.9,
    "bloomberg": 0.9,
    "yfinance": 0.8,
    "financial times": 0.9,
    "techcrunch": 0.8,
    "wired": 0.8,
    "the verge": 0.7,
    "cnbc": 0.8,
    "default": 0.5,  # Fonti sconosciute o generiche
}


def calculate_freshness_score(
    published_date_str: str, reference_time: datetime = None
) -> float:
    """
    Calcola un decadimento temporale (Time Decay).
    Oggi/Ieri = punteggio alto. >2 giorni = punteggio crolla.
    """
    if not published_date_str or str(published_date_str).strip() == "":
        return 0.5  # Neutro se manca la data

    try:
        # SECURITY/EVAL FIX: Usa reference_time se fornito (per i benchmark), altrimenti usa now()
        now = reference_time or datetime.now(timezone.utc)

        # Gestione fallback per stringhe non formattate
        if (
            "oggi" in str(published_date_str).lower()
            or "today" in str(published_date_str).lower()
        ):
            return 1.0

        article_date = dateutil.parser.parse(str(published_date_str))
        if article_date.tzinfo is None:
            article_date = article_date.replace(tzinfo=timezone.utc)

        diff_hours = (now - article_date).total_seconds() / 3600

        if diff_hours <= 12:
            return 1.0
        elif diff_hours <= 24:
            return 0.8
        elif diff_hours <= 48:
            return 0.5
        else:
            return 0.2
    except Exception as e:
        logger.debug(f"Errore parsing data per freshness: {e}")
        return 0.5


def calculate_source_score(source_name: str) -> float:
    """Assegna un punteggio basato sull'autorevolezza della fonte."""
    if not source_name:
        return SOURCE_QUALITY_WEIGHTS["default"]

    source_lower = str(source_name).lower()
    for key, weight in SOURCE_QUALITY_WEIGHTS.items():
        if key in source_lower:
            return weight

    return SOURCE_QUALITY_WEIGHTS["default"]


def score_and_filter_candidates(
    news_list: list, max_candidates: int = 20, reference_time: datetime = None
) -> list:
    """
    Pipeline deterministica: valuta tutti gli articoli e restituisce i Top K
    con i metadati dei punteggi esposti in modo trasparente.
    """
    if not news_list:
        return []

    scored_news = []

    for item in news_list:
        # 1. Estrazione metriche passando il reference_time
        freshness = calculate_freshness_score(
            item.get("published", ""), reference_time=reference_time
        )
        source_quality = calculate_source_score(item.get("source", ""))

        # 2. Formula Deterministica Composita (Customizzabile)
        # 60% peso sull'autorevolezza della fonte, 40% sulla novità
        composite_score = (0.60 * source_quality) + (0.40 * freshness)

        # Normalizziamo a 100
        final_score_100 = round(composite_score * 100, 2)

        # 3. Arricchiamo il dizionario per l'Observability
        item["deterministic_score"] = final_score_100
        item["score_breakdown"] = {
            "freshness": freshness,
            "source_quality": source_quality,
        }
        scored_news.append(item)

    # Ordiniamo in base al punteggio deterministico
    scored_news = sorted(
        scored_news, key=lambda x: x["deterministic_score"], reverse=True
    )

    # Ritorna solo i Top N candidati per limitare i token passati all'LLM
    top_candidates = scored_news[:max_candidates]
    logger.info(
        f"Deterministic Filtering completed. Reduced {len(news_list)} items to Top {len(top_candidates)} candidates."
    )

    return top_candidates
