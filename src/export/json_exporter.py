import os
import json
import logging
import re
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timezone
from typing import List, Dict
from pydantic import BaseModel, Field, ValidationError

logger = logging.getLogger(__name__)

class BriefingItem(BaseModel):
    id: str
    title: str
    summary: str
    source_name: str
    source_url: str
    published_at: str
    entities: List[str] = []

class Connection(BaseModel):
    id: str
    item_ids: List[str]
    hypothesis: str
    confidence: str = Field(pattern="^(bassa|media|alta)$")

class BriefingSchema(BaseModel):
    schema_version: int = 1
    generated_at: str
    date_label: str
    narrative_briefing: str = ""
    domains: Dict[str, List[BriefingItem]]
    connections: List[Connection]

class JsonExporter:
    def __init__(self, base_dir: str):
        self.docs_dir = os.path.join(base_dir, "docs")
        self.archive_dir = os.path.join(self.docs_dir, "data", "archive")
        os.makedirs(self.archive_dir, exist_ok=True)
        
        self.latest_file = os.path.join(self.docs_dir, "latest_briefing.json")
        self.index_file = os.path.join(self.archive_dir, "index.json")

    def _map_domain(self, area: str) -> str:
        area = area.upper()
        if area == "FINANZA": return "markets"
        if area in ["RICERCA", "TECH"]: return "ai_research"
        return "news_politics" 

    def _scrape_url_for_text(self, url: str) -> str:
        """Secretly opens the news link and extracts the full text."""
        try:
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
            resp = requests.get(url, headers=headers, timeout=4)
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.text, 'html.parser')
                paragraphs = soup.find_all('p')
                text = " ".join([p.text for p in paragraphs])
                return text.strip()
        except Exception:
            pass
        return ""

    def _extract_best_summary(self, item: Dict) -> str:
        candidates = [
            str(item.get("content", "")),
            str(item.get("content:encoded", "")),
            str(item.get("description", "")),
            str(item.get("summary", ""))
        ]
        
        best_text = ""
        for c in candidates:
            if c and c.strip() and c != "None":
                clean_c = re.sub(r'<[^>]*>?', '', c).strip()
                clean_c = re.sub(r'\s+', ' ', clean_c)
                if len(clean_c) > len(best_text):
                    best_text = clean_c
        
        if len(best_text) < 300 and item.get("url"):
            scraped_text = self._scrape_url_for_text(item["url"])
            if len(scraped_text) > len(best_text):
                best_text = scraped_text

        best_text = re.sub(r'\s+', ' ', best_text).strip()
        
        if len(best_text) < 15:
            return "Operational details restricted. Please consult the primary source for full intelligence."
            
        if len(best_text) > 700:
            return best_text[:697] + "..."
            
        return best_text

    def export(self, ranked_news: List[Dict], insights_data: List[Dict], narrative_briefing: str) -> bool:
        logger.info("Starting JSON export with Live Text Scraping and 700-character limit...")
        now = datetime.now(timezone.utc)
        date_str = now.strftime('%Y-%m-%d')
        
        domains_dict = {"ai_research": [], "markets": [], "news_politics": []}

        for idx, item in enumerate(ranked_news):
            item_id = item.get("id", f"item-{date_str}-{idx}")
            domain_key = self._map_domain(item.get("area", "MIX"))
            
            final_summary = self._extract_best_summary(item)
            
            briefing_item = BriefingItem(
                id=item_id,
                title=item.get("title", "Untitled"),
                summary=final_summary,
                source_name=item.get("source", "Web"),
                source_url=item.get("url", "#"),
                published_at=item.get("published", now.isoformat())
            )
            domains_dict[domain_key].append(briefing_item)

        connections = []
        for idx, conn_data in enumerate(insights_data):
            target_id = conn_data.get("target_id")
            insight_text = conn_data.get("insight", "")
            
            if target_id and insight_text:
                conn = Connection(
                    id=f"conn-{date_str}-{idx}",
                    item_ids=[target_id],
                    hypothesis=insight_text,
                    confidence="alta"
                )
                connections.append(conn)

        payload = {
            "schema_version": 1,
            "generated_at": now.isoformat(),
            "date_label": now.strftime("%d %B %Y"),
            "narrative_briefing": narrative_briefing,
            "domains": domains_dict,
            "connections": connections
        }

        try:
            validated_data = BriefingSchema(**payload)
        except ValidationError as e:
            logger.error(f"JSON Validation failed! Details:\n{e}")
            return False

        json_str = validated_data.model_dump_json(indent=2)
        
        with open(self.latest_file, "w", encoding="utf-8") as f:
            f.write(json_str)
            
        # Write to historical archive
        archive_file = os.path.join(self.archive_dir, f"{date_str}.json")
        with open(archive_file, "w", encoding="utf-8") as f:
            f.write(json_str)
            
        self._update_archive_index(date_str)
        return True

    def _update_archive_index(self, new_date: str):
        dates = []
        if os.path.exists(self.index_file):
            try:
                with open(self.index_file, "r") as f:
                    dates = json.load(f)
            except: pass
        if new_date not in dates:
            dates.append(new_date)
            dates.sort(reverse=True)
        with open(self.index_file, "w") as f:
            json.dump(dates, f, indent=2)