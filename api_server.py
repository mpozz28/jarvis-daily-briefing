import json
import logging

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

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
    question: str


@app.post("/api/ask")
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

    # 3. Formattazione dell'HTML finale per il frontend
    base_answer = qa_result.get("answer", "Error in cognitive response.")
    evidence = qa_result.get("evidence")
    confidence = qa_result.get("confidence", 0.0)

    final_html = base_answer

    # Aggiunge il blocco citazione testuale se presente (il frontend lo renderizzerà)
    if evidence and confidence > 0.0:
        final_html += "<br><br><span style='font-size: 0.8rem; color: var(--muted-ink); border-left: 2px solid var(--blueprint-blue); padding-left: 8px; display: block;'>"
        final_html += (
            f"<b>Grounding Evidence (Conf: {confidence}):</b> <em>'{evidence}'</em>"
        )

        if target_item and target_item.get("source_url"):
            final_html += f" <br><a href='{target_item['source_url']}' target='_blank' style='color: var(--blueprint-blue); text-decoration: none;'>[Verify Source]</a>"

        final_html += "</span>"

    return {
        "answer": final_html,  # Il sintetizzatore vocale leggerà la risposta, l'HTML mostrerà le prove
        "target_id": target_item.get("id") if target_item else None,
    }


# Mount static files to serve the Web UI directly from the API
app.mount("/", StaticFiles(directory="docs", html=True), name="docs")

if __name__ == "__main__":
    print("=" * 60)
    print("🚀 J.A.R.V.I.S. API Server Active at http://localhost:8000")
    print("🔒 Zero-Hallucination Evidence Layer Online")
    print("=" * 60)
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="warning")
