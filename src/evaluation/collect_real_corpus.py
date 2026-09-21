import argparse
import hashlib
import html
import json
import os
import re
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

import dateutil.parser
import feedparser

DEFAULT_FEEDS = {
    "BBC_World": {"url": "http://feeds.bbci.co.uk/news/world/rss.xml", "area_hint": "WORLD"},
    "Al_Jazeera_Global": {"url": "https://www.aljazeera.com/xml/rss/all.xml", "area_hint": "WORLD"},
    "NYT_US_News": {"url": "https://rss.nytimes.com/services/xml/rss/nyt/US.xml", "area_hint": "POLITICS"},
    "NYT_Business": {"url": "https://rss.nytimes.com/services/xml/rss/nyt/Business.xml", "area_hint": "FINANCE"},
    "Politico_US": {"url": "https://rss.politico.com/politics-news.xml", "area_hint": "POLITICS"},
    "NPR_Top_Stories": {"url": "https://feeds.npr.org/1001/rss.xml", "area_hint": "WORLD"},
    "TechCrunch": {"url": "https://techcrunch.com/feed/", "area_hint": "TECH"},
    "Ars_Technica": {"url": "https://feeds.arstechnica.com/arstechnica/index", "area_hint": "TECH"},
    "ArXiv_AI": {"url": "https://export.arxiv.org/rss/cs.AI", "area_hint": "AI/ML"},
    "ArXiv_ML": {"url": "https://export.arxiv.org/rss/cs.LG", "area_hint": "AI/ML"},
}

TRACKING_PARAMS = {"fbclid", "gclid", "mc_cid", "mc_eid", "ref"}


def normalize_url(url: str) -> str:
    if not url:
        return ""
    parts = urlsplit(url.strip())
    if not parts.scheme or not parts.netloc:
        return url.strip().rstrip("/")
    query = [(k, v) for k, v in parse_qsl(parts.query, keep_blank_values=True)
             if k.lower() not in TRACKING_PARAMS and not k.lower().startswith("utm_")]
    path = parts.path.rstrip("/") or "/"
    return urlunsplit((parts.scheme.lower(), parts.netloc.lower(), path, urlencode(query), ""))


def normalize_text(text: str) -> str:
    text = html.unescape(re.sub(r"<[^>]+>", " ", text or ""))
    return re.sub(r"\s+", " ", text).strip()


def parse_published(entry: dict) -> str:
    parsed = entry.get("published_parsed") or entry.get("updated_parsed")
    if parsed:
        dt = datetime(parsed.tm_year, parsed.tm_mon, parsed.tm_mday, parsed.tm_hour,
                      parsed.tm_min, parsed.tm_sec, tzinfo=timezone.utc)
        return dt.isoformat()
    raw = entry.get("published") or entry.get("updated") or entry.get("pubDate") or entry.get("date") or ""
    if not raw:
        return ""
    for parser in (parsedate_to_datetime, dateutil.parser.parse):
        try:
            dt = parser(str(raw))
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt.astimezone(timezone.utc).isoformat()
        except (TypeError, ValueError, OverflowError):
            continue
    return ""


def classify_area(title: str, summary: str, area_hint: str) -> str:
    text = f"{title} {summary}".lower()
    if area_hint == "AI/ML":
        return "AI/ML"
    if area_hint == "TECH" and not any(k in text for k in ("stock", "shares", "market", "fed ", "interest rate", "inflation")):
        return "TECH"
    groups = [
        ("AI/ML", ("artificial intelligence", "machine learning", "generative ai", "large language model", "llm", "neural network", "deep learning", "openai", "anthropic", "nvidia")),
        ("FINANCE", ("stock", "shares", "market", "markets", "federal reserve", "interest rate", "inflation", "gdp", "bond", "earnings", "bitcoin", "crypto", "recession")),
        ("SCIENCE", ("scientist", "scientists", "research", "study", "space", "nasa", "physics", "biology", "climate")),
        ("POLITICS", ("election", "president", "senate", "congress", "parliament", "government", "minister", "policy", "political")),
        ("WORLD", ("war", "ukraine", "gaza", "iran", "israel", "russia", "china", "european union", "nato", "international")),
        ("TECH", ("technology", "software", "startup", "chip", "semiconductor", "cybersecurity", "robot", "cloud", "apple", "microsoft")),
    ]
    for area, keywords in groups:
        if any(k in text for k in keywords):
            return area
    return area_hint if area_hint in {"TECH", "AI/ML", "FINANCE", "SCIENCE", "WORLD", "POLITICS"} else "OTHER"


def article_id(canonical_url: str, title: str, source: str) -> str:
    seed = canonical_url or f"{source}|{title.lower()}"
    return hashlib.sha256(seed.encode("utf-8")).hexdigest()[:16]


def collect_feed(name: str, config: dict, per_source: int) -> tuple[list[dict], str | None]:
    try:
        feed = feedparser.parse(config["url"])
        if getattr(feed, "bozo", False) and not feed.entries:
            return [], f"feed parse error: {getattr(feed, 'bozo_exception', 'unknown')}"
    except Exception as exc:
        return [], str(exc)
    items, seen = [], set()
    for entry in feed.entries[:per_source]:
        title = normalize_text(entry.get("title", "Untitled"))
        raw_summary = entry.get("summary") or entry.get("description") or ""
        if entry.get("content"):
            raw_summary = entry["content"][0].get("value", raw_summary)
        summary = normalize_text(raw_summary)
        url = str(entry.get("link", "")).strip()
        canonical = normalize_url(url)
        if not title or not canonical or canonical in seen:
            continue
        seen.add(canonical)
        items.append({
            "id": article_id(canonical, title, name),
            "title": title,
            "summary": summary[:2000],
            "area": classify_area(title, summary, config["area_hint"]),
            "source": name,
            "published": parse_published(entry),
            "url": url,
            "canonical_url": canonical,
            "duplicate_group": None,
            "split": None,
            "annotation_version": None,
            "annotator_ids": [],
            "annotated_at": None,
            "notes": "",
        })
    return items, None


def assign_temporal_split(items: list[dict], test_days: int) -> None:
    dates = []
    for item in items:
        try:
            if item["published"]:
                dates.append(dateutil.parser.isoparse(item["published"]))
        except (TypeError, ValueError):
            pass
    if not dates:
        for item in items:
            item["split"] = "dev"
        return
    newest = max(dates)
    cutoff = newest.timestamp() - test_days * 86400
    for item in items:
        try:
            dt = dateutil.parser.isoparse(item["published"])
            item["split"] = "test" if dt.timestamp() >= cutoff else "dev"
        except (TypeError, ValueError):
            item["split"] = "dev"


def collect_corpus(per_source: int, max_items: int, test_days: int) -> tuple[list[dict], dict]:
    all_items, source_stats = [], {}
    for name, config in DEFAULT_FEEDS.items():
        items, error = collect_feed(name, config, per_source)
        source_stats[name] = {"requested": per_source, "collected": len(items), "error": error}
        all_items.extend(items)
    unique = {}
    for item in all_items:
        unique.setdefault(item["canonical_url"] or item["id"], item)
    corpus = sorted(unique.values(), key=lambda x: x["published"], reverse=True)[:max_items]
    assign_temporal_split(corpus, test_days)
    manifest = {
        "collected_at": datetime.now(timezone.utc).isoformat(),
        "feed_count": len(DEFAULT_FEEDS),
        "per_source_limit": per_source,
        "max_items": max_items,
        "test_window_days": test_days,
        "raw_items": len(all_items),
        "final_items": len(corpus),
        "sources": source_stats,
        "label_status": "unannotated",
        "gold_relevance_present": False,
    }
    return corpus, manifest


def main() -> None:
    parser = argparse.ArgumentParser(description="Collect real RSS articles for manual J.A.R.V.I.S. ranking annotation.")
    parser.add_argument("--per-source", type=int, default=50)
    parser.add_argument("--max-items", type=int, default=500)
    parser.add_argument("--test-days", type=int, default=2)
    parser.add_argument("--output", default="eval/real_corpus_unannotated.json")
    parser.add_argument("--manifest", default="eval/real_corpus_manifest.json")
    args = parser.parse_args()
    corpus, manifest = collect_corpus(args.per_source, args.max_items, args.test_days)
    os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as handle:
        json.dump(corpus, handle, indent=2, ensure_ascii=False)
    with open(args.manifest, "w", encoding="utf-8") as handle:
        json.dump(manifest, handle, indent=2, ensure_ascii=False)
    print(f"Collected {len(corpus)} unique articles from {len(DEFAULT_FEEDS)} feeds. Unannotated output: {args.output}")


if __name__ == "__main__":
    main()
