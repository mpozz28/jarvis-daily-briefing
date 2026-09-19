import os
import logging
import re
import time
from src.utils.observability import logger, metrics_tracker
from typing import TypedDict, List, Dict
from langgraph.graph import StateGraph, END
from dotenv import load_dotenv
from datetime import datetime, timezone
import dateutil.parser

# Initialize Environment & Logger
load_dotenv()
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger("JarvisOrchestrator")

# Import Agents and Modules
from src.agents.research_agent import fetch_research, fetch_tech_news
from src.agents.markets_agent import fetch_markets, fetch_market_news
from src.agents.news_agent import fetch_news
from src.agents.ranking_agent import rank_and_filter
from src.agents.connect_dots_agent import connect_the_dots
from src.agents.writer_agent import write_jarvis_briefing
from src.memory.sqlite_store import is_already_seen, save_seen_article
from src.export.json_exporter import JsonExporter

class JarvisState(TypedDict):
    raw_news: List[Dict]          
    ranked_news: List[Dict]       
    insights: List[Dict]          
    final_briefing: str           

def generate_id_hash(title: str) -> str:
    """Generates a clean string ID from a title."""
    return re.sub(r'[^a-z0-9]', '', str(title).lower())

def is_recent(date_string: str, max_days: int = 2) -> bool:
    """Checks if the news article falls within the acceptable timeframe."""
    if not date_string or str(date_string).strip() == "":
        return False 
    
    now = datetime.now(timezone.utc)
    try:
        if "oggi" in str(date_string).lower() or "today" in str(date_string).lower():
            return True
            
        article_date = dateutil.parser.parse(str(date_string))
        if article_date.tzinfo is None:
            article_date = article_date.replace(tzinfo=timezone.utc)
            
        diff = now - article_date
        return diff.days <= max_days
    except Exception:
        return False 

def collection_node(state: JarvisState) -> dict:
    logger.info("--- NODE 1: MULTI-AGENT DATA COLLECTION ---")
    raw = []
    raw.extend(fetch_research())
    raw.extend(fetch_tech_news())
    raw.extend(fetch_markets())
    raw.extend(fetch_market_news())
    raw.extend(fetch_news())
    
    filtered_raw = []
    discarded_count = 0
    
    for item in raw:
        article_date = item.get("published", item.get("updated", ""))
        id_hash = generate_id_hash(item.get("title", ""))
        
        if not is_recent(article_date):
            discarded_count += 1
            continue
            
        if not is_already_seen(id_hash):
            filtered_raw.append(item)
            
    logger.info(f"Collected: {len(raw)}. Discarded (old): {discarded_count}. To evaluate: {len(filtered_raw)}")
    return {"raw_news": filtered_raw}

def ranking_node(state: JarvisState) -> dict:
    logger.info("--- NODE 2: RANKING & FILTERING ---")
    ranked = rank_and_filter(state["raw_news"])
    
    # Store selected news in memory to avoid future repetitions
    for item in ranked:
        id_hash = generate_id_hash(item.get("title", ""))
        save_seen_article(id_hash, item.get("title", "No Title"), item.get("source", "Unknown"))
        
    return {"ranked_news": ranked}

def connect_dots_node(state: JarvisState) -> dict:
    logger.info("--- NODE 3: MACRO-TREND CORRELATION ---")
    insights = connect_the_dots(state["ranked_news"])
    return {"insights": insights}

def writer_node(state: JarvisState) -> dict:
    logger.info("--- NODE 4: NARRATIVE BRIEFING GENERATION ---")
    briefing = write_jarvis_briefing(state["ranked_news"], state["insights"])
    return {"final_briefing": briefing}

def export_node(state: JarvisState) -> dict:
    logger.info("--- NODE 5: JSON EXPORT FOR WEB APP ---")
    base_dir = os.path.dirname(os.path.dirname(__file__))
    exporter = JsonExporter(base_dir=base_dir)
    
    narrative_text = state.get("final_briefing", "")
    if not narrative_text:
        logger.warning("WARNING: No narrative text found. Exporter triggered prematurely?")
        
    exporter.export(state["ranked_news"], state["insights"], narrative_text)
    return {}

def build_graph():
    """Builds and compiles the LangGraph state machine."""
    workflow = StateGraph(JarvisState)
    
    workflow.add_node("collect", collection_node)
    workflow.add_node("rank", ranking_node)
    workflow.add_node("connect", connect_dots_node)
    workflow.add_node("write", writer_node)
    workflow.add_node("export", export_node)
    
    workflow.set_entry_point("collect")
    workflow.add_edge("collect", "rank")
    workflow.add_edge("rank", "connect")
    workflow.add_edge("connect", "write")
    workflow.add_edge("write", "export") 
    workflow.add_edge("export", END)
    
    return workflow.compile()

if __name__ == "__main__":
    logger.info("Initializing J.A.R.V.I.S. Core Systems...", extra={"component": "orchestrator"})
    app = build_graph()
    initial_state = {"raw_news": [], "ranked_news": [], "insights": [], "final_briefing": ""}
    
    start_time = time.time()
    try:
        # Avvia la pipeline di LangGraph
        app.invoke(initial_state)
        
        latency = time.time() - start_time
        summary = metrics_tracker.get_summary()
        
        # Log finale STRUTTURATO con tutte le metriche della run
        logger.info(
            "Pipeline execution completed successfully. Data exported to Web App.",
            extra={
                "component": "orchestrator",
                "metrics": {
                    "total_latency_sec": round(latency, 2),
                    "llm_stats": summary
                }
            }
        )
        
    except Exception as e:
        logger.error(
            f"Errore critico nella pipeline: {str(e)}", 
            exc_info=True, 
            extra={"component": "orchestrator"}
        )
        raise e