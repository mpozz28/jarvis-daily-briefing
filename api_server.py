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
    executive_summary = ""
    connections_text = ""
    
    # 1. Caricamento del Contesto
    try:
        with open("docs/latest_briefing.json", "r", encoding="utf-8") as f:
            data = json.load(f)
            
            executive_summary = data.get("narrative_briefing", "")
            
            connections = data.get("connections", [])
            if isinstance(connections, list) and connections:
                connections_text = "\n--- SYSTEM CORRELATIONS ---\n"
                for c in connections:
                    if isinstance(c, dict):
                        connections_text += f"- {c.get('description', '') or c.get('summary', '') or str(c)}\n"
                    else:
                        connections_text += f"- {str(c)}\n"

            for domain, items in data.get("domains", {}).items():
                ranked_news.extend(items)
                
        logger.info(f"Caricato narrative_briefing: {len(executive_summary)} caratteri")
    except Exception as e:
        logger.error(f"Failed to read latest_briefing.json context: {e}")

    # 2. Routing
    target_item = qa_agent.identify_relevant_item(request.question, ranked_news, executive_summary)

    # 3. Costruzione del Contesto Completo
    item_summary = target_item.get("summary", "") if target_item else ""
    full_text_context = f"{executive_summary}\n\n{connections_text}\n\n{item_summary}".strip()
    
    # 4. Grounded Generation (Questa è la chiamata all'LLM che era saltata!)
    qa_result = qa_agent.answer_question(
        question=request.question, 
        target_item=target_item, 
        source_text=full_text_context, 
        context=""
    )

    # 5. Estrazione Dati per Frontend e Sintesi Vocale
    base_answer = qa_result.get("answer", "Error in cognitive response.")
    evidence = qa_result.get("evidence")
    confidence = qa_result.get("confidence", 0.0)

    # 6. Costruzione del blocco visivo (solo HTML)
    html_answer = base_answer
    if evidence and confidence > 0.0:
        html_answer += f"<br><br><span style='font-size:0.85rem; color:var(--muted-ink); border-left: 2px solid var(--blueprint-blue); padding-left: 8px; display: block; margin-top: 8px;'><b>[Verified Evidence]:</b> <i>\"{evidence}\"</i><br><b>[Composite Confidence]:</b> {confidence}%</span>"

    return {
        "spoken_answer": base_answer,  # J.A.R.V.I.S. leggerà solo questo (Testo pulito)
        "html_answer": html_answer,    # Lo schermo visualizzerà questo (Testo + Badge formattato)
        "target_id": target_item.get("id") if target_item else None,
        "confidence": confidence
    }


# Mount static files to serve the Web UI directly from the API
app.mount("/", StaticFiles(directory="docs", html=True), name="docs")
if __name__ == "__main__":
    print("=" * 60)
    print("🚀 J.A.R.V.I.S. API Server Active at http://localhost:8000")
    print("🔒 Zero-Hallucination Evidence Layer Online")
    print("=" * 60)
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="warning") 

