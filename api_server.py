import json
import logging

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from src.agents.qa_agent import QAAgent

# Setup Logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("JarvisAPI")

app = FastAPI(title="J.A.R.V.I.S. API Server")

# 🔒 SECURITY FIX: Restricted CORS Policy
ALLOWED_ORIGINS = [
    "http://localhost:8000",
    "http://127.0.0.1:8000",
    "https://mpozz28.github.io",  # Solo la tua pagina web può chiamare l'API!
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

# Initialize Q&A Engine
qa_agent = QAAgent()


class ChatRequest(BaseModel):
    question: str = Field(min_length=1, max_length=2000)


class ChatResponse(BaseModel):
    answer: str
    target_id: str | None = None
    evidence: str | None = None
    confidence: float = 0.0
    supported: bool = False
    source_url: str | None = None
    retrieval_method: str | None = None


@app.post("/api/ask", response_model=ChatResponse)
def ask_jarvis(request: ChatRequest):
    logger.info(f"User Query Received: {request.question}")

    ranked_news = []
    try:
        with open("docs/latest_briefing.json", "r", encoding="utf-8") as f:
            data = json.load(f)
            for domain, items in data.get("domains", {}).items():
                ranked_news.extend(items)
    except Exception as e:
        logger.error(f"Failed to read latest_briefing.json context: {e}")

    # 1. Routing
    target_item = qa_agent.identify_relevant_item(request.question, ranked_news, "")

    # 2. Grounded Generation (Restituisce un Dictionary)
    source_text = target_item.get("summary", "") if target_item else ""
    qa_result = qa_agent.answer_question(request.question, target_item, source_text, "")

    # 3. Return structured data. Presentation stays in the frontend.
    return {
        "answer": qa_result.get("answer", "Error in cognitive response."),
        "target_id": target_item.get("id") if target_item else None,
        "evidence": qa_result.get("evidence"),
        "confidence": qa_result.get("confidence", 0.0),
        "supported": qa_result.get("supported", False),
        "source_url": qa_result.get("source_url"),
        "retrieval_method": qa_result.get("retrieval_method"),
    }


# Mount static files to serve the Web UI directly from the API
app.mount("/", StaticFiles(directory="docs", html=True), name="docs")

if __name__ == "__main__":
    print("=" * 60)
    print("🚀 J.A.R.V.I.S. API Server Active at http://localhost:8000")
    print("🔒 Evidence-Grounded QA Layer Online")
    print("=" * 60)
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="warning")
