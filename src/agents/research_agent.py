import logging
import feedparser
import re
import concurrent.futures
from typing import List, Dict
from src.memory.source_cache import source_cache
from src.config import RESEARCH_FEEDS

logger = logging.getLogger(__name__)

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

def fetch_research() -> List[Dict]:
    """Extracts the latest scientific papers from ArXiv feeds."""
    research_items = []
    
    for category, url in RESEARCH_FEEDS.items():
        logger.info(f"Collecting papers from {category}...")
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:10]:
                date_str = get_real_date(entry) 
                
                research_items.append({
                    "id": entry.link,
                    "title": entry.title.replace('\n', ' '),
                    "summary": entry.summary.replace('\n', ' ')[:500] + "...", 
                    "domain": "Research AI",
                    "source": category,
                    "url": entry.link,
                    "published": date_str
                })
        except Exception as e:
            logger.error(f"Error parsing feed {category}: {e}")
            
    return research_items

TECH_SOURCES = {
    "TechCrunch": "https://techcrunch.com/feed/",
    "Ars_Technica": "https://feeds.arstechnica.com/arstechnica/index",
    "MIT_Tech_Review": "https://www.technologyreview.com/feed/",
    "Scientific_American": "http://rss.sciam.com/ScientificAmerican-Global"
}

def _fetch_tech_source(name: str, url: str, max_per_source: int) -> List[Dict]:
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

def fetch_tech_news(max_per_source: int = 8) -> List[Dict]:
    """Orchestrates parallel fetching of tech and innovation news."""
    logger.info("Starting Tech & Innovation collection (Parallel execution)...")
    tech_news = []
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(_fetch_tech_source, name, url, max_per_source) for name, url in TECH_SOURCES.items()]
        for future in concurrent.futures.as_completed(futures):
            tech_news.extend(future.result())
            
    return tech_news