import json
import logging
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

from src.agents.qa_agent import QAAgent

# Setup Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("JarvisAPI")

app = FastAPI(title="J.A.R.V.I.S. API Server")

# CORS Configuration for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Q&A Engine
qa_agent = QAAgent()

class ChatRequest(BaseModel):
    question: str

@app.post("/api/ask")
def ask_jarvis(request: ChatRequest):
    logger.info(f"User Query Received: {request.question}")
    
    ranked_news = []
    try:
        # Load today's briefing to provide context to the LLM
        with open("docs/latest_briefing.json", "r", encoding="utf-8") as f:
            data = json.load(f)
            for domain, items in data.get("domains", {}).items():
                ranked_news.extend(items)
    except Exception as e:
        logger.error(f"Failed to read latest_briefing.json context: {e}")
        
    # 1. Routing: Identify target news
    target_item = qa_agent.identify_relevant_item(request.question, ranked_news, "")
    
    # 2. Generation: Formulate answer with live web scraping fallback
    source_text = target_item.get("summary", "") if target_item else ""
    answer = qa_agent.answer_question(request.question, target_item, source_text, "")
    
    return {
        "answer": answer,
        "target_id": target_item.get("id") if target_item else None
    }

# Mount static files to serve the Web UI directly from the API
app.mount("/", StaticFiles(directory="docs", html=True), name="docs")

if __name__ == "__main__":
    print("="*60)
    print("🚀 J.A.R.V.I.S. API Server Active at http://localhost:8000")
    print("="*60)
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="warning")