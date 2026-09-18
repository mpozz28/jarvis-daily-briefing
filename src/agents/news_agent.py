import feedparser
import re
import logging
import concurrent.futures
from typing import List, Dict

logger = logging.getLogger(__name__)

NEWS_SOURCES = {
    "BBC_World": "http://feeds.bbci.co.uk/news/world/rss.xml",
    "Al_Jazeera_Global": "https://www.aljazeera.com/xml/rss/all.xml",
    "NYT_US_News": "https://rss.nytimes.com/services/xml/rss/nyt/US.xml",
    "Politico_US": "https://rss.politico.com/politics-news.xml",
    "NPR_Top_Stories": "https://feeds.npr.org/1001/rss.xml"
}

def get_real_date(entry: dict) -> str:
    """Extracts the publication date from various possible RSS keys."""
    possible_keys = [
        "published", "updated", "pubDate", "published_at", "publishedAt", 
        "date", "created_at", "time_published", "dc:date"
    ]
    for key in possible_keys:
        val = entry.get(key)
        if val: 
            return str(val)
    return ""

def _fetch_source(name: str, url: str, max_per_source: int) -> List[Dict]:
    """Fetches and parses a single RSS feed."""
    results = []
    try:
        feed = feedparser.parse(url)
        for entry in feed.entries[:max_per_source]:
            desc = re.sub('<[^<]+>', '', entry.get("description", ""))
            date_str = get_real_date(entry)
            
            results.append({
                "id": entry.get("link", ""),
                "source": name,
                "domain": name,
                "title": entry.get("title", "Untitled"),
                "description": desc[:200] + "..." if len(desc) > 200 else desc,
                "url": entry.get("link", ""),
                "published": date_str
            })
    except Exception as e:
        logger.warning(f"Error fetching {name}: {e}")
    return results

def fetch_news(max_per_source: int = 8) -> List[Dict]:
    """Orchestrates parallel fetching of global news."""
    logger.info("Starting Geopolitics collection (Parallel execution)...")
    all_news = []
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(_fetch_source, name, url, max_per_source) for name, url in NEWS_SOURCES.items()]
        for future in concurrent.futures.as_completed(futures):
            all_news.extend(future.result())
            
    return all_news