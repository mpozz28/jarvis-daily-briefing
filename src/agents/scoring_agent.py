import logging
from collections import Counter
from datetime import datetime, timezone

import dateutil.parser

logger = logging.getLogger(__name__)

SOURCE_QUALITY_WEIGHTS = {
    "arxiv": 0.65,
    "reuters": 0.9,
    "bloomberg": 0.9,
    "yfinance": 0.8,
    "financial times": 0.9,
    "techcrunch": 0.8,
    "wired": 0.8,
    "the verge": 0.7,
    "cnbc": 0.8,
    "default": 0.5,
}

GROUP_CAPS = {"research": 3, "tech": 5, "news": 6, "finance": 5}
SOURCE_CAP = 3


def calculate_freshness_score(published_date_str: str, reference_time: datetime = None) -> float:
    if not published_date_str or not str(published_date_str).strip():
        return 0.5
    try:
        now = reference_time or datetime.now(timezone.utc)
        if any(word in str(published_date_str).lower() for word in ("oggi", "today")):
            return 1.0
        article_date = dateutil.parser.parse(str(published_date_str))
        if article_date.tzinfo is None:
            article_date = article_date.replace(tzinfo=timezone.utc)
        diff_hours = (now - article_date).total_seconds() / 3600
        if diff_hours <= 12:
            return 1.0
        if diff_hours <= 24:
            return 0.8
        if diff_hours <= 48:
            return 0.5
        return 0.2
    except Exception as exc:
        logger.debug("Date parsing failed: %s", exc)
        return 0.5


def calculate_source_score(source_name: str) -> float:
    source_lower = str(source_name or "").lower()
    for key, weight in SOURCE_QUALITY_WEIGHTS.items():
        if key in source_lower:
            return weight
    return SOURCE_QUALITY_WEIGHTS["default"]


def classify_content_group(item: dict) -> str:
    source = str(item.get("source", "")).lower()
    domain = str(item.get("domain", "")).lower()
    area = str(item.get("area", "")).lower()
    if "arxiv" in source or "research" in domain or "ricerca" in area:
        return "research"
    if any(x in source for x in ("yahoo finance", "wsj_", "cnbc_", "economist")) or "finance" in domain or "finanza" in area:
        return "finance"
    if area == "tech" or "tech" in domain or any(x in source for x in ("techcrunch", "ars_", "mit_tech", "scientific")):
        return "tech"
    return "news"


def select_diverse_items(items: list[dict], limit: int) -> list[dict]:
    selected, group_counts, source_counts, selected_ids = [], Counter(), Counter(), set()
    groups = ["news", "tech", "finance", "research"]
    for group in groups:
        for item in items:
            item_id = str(item.get("id", ""))
            source = str(item.get("source", "")).lower()
            if item_id in selected_ids or classify_content_group(item) != group:
                continue
            if group_counts[group] >= GROUP_CAPS[group] or source_counts[source] >= SOURCE_CAP:
                continue
            selected.append(item)
            selected_ids.add(item_id)
            group_counts[group] += 1
            source_counts[source] += 1
            break
    for item in items:
        if len(selected) >= limit:
            break
        item_id = str(item.get("id", ""))
        source = str(item.get("source", "")).lower()
        group = classify_content_group(item)
        if item_id in selected_ids or group_counts[group] >= GROUP_CAPS[group] or source_counts[source] >= SOURCE_CAP:
            continue
        selected.append(item)
        selected_ids.add(item_id)
        group_counts[group] += 1
        source_counts[source] += 1
    return selected


def score_and_filter_candidates(news_list: list, max_candidates: int = 20, reference_time: datetime = None) -> list:
    if not news_list:
        return []
    scored = []
    for item in news_list:
        freshness = calculate_freshness_score(item.get("published", ""), reference_time)
        source_quality = calculate_source_score(item.get("source", ""))
        item["deterministic_score"] = round((0.60 * source_quality + 0.40 * freshness) * 100, 2)
        item["score_breakdown"] = {"freshness": freshness, "source_quality": source_quality}
        scored.append(item)
    scored.sort(key=lambda item: item["deterministic_score"], reverse=True)
    return select_diverse_items(scored, max_candidates) if len(scored) > max_candidates else scored
