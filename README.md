# 🧠 J.A.R.V.I.S. - Enterprise AI Intelligence Platform

![Python](https://img.shields.io/badge/Python-3.12-blue)
![LangGraph](https://img.shields.io/badge/Orchestration-LangGraph-orange)
![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688)
![Evaluation](https://img.shields.io/badge/Evaluation-NDCG%403%3D1.0-brightgreen)
![Status](https://img.shields.io/badge/Status-Production_Ready-success)

> **Elevator Pitch:** An evidence-grounded AI intelligence platform that aggregates heterogeneous data (News, Research, Market Metrics), ranks them using an LLM-as-a-Judge pattern, calculates deterministic financial metrics via Pandas, and serves a zero-hallucination UI through a fully observable LangGraph/FastAPI pipeline.

## 🏗️ System Architecture

J.A.R.V.I.S. is built on a **Hybrid Deterministic/LLM Architecture**, ensuring that math is done by code, and reasoning is done by AI.

```mermaid
graph TD
    %% Ingestion
    A[Cron Job / GitHub Actions] --> B(Data Collection Node)
    B -->|RSS / Web Scraping| C(SQLite Memory Deduplication)
    
    %% Processing
    C --> D(LLM-as-a-Judge Ranking)
    D --> E(Quantitative Finance Module)
    E -->|Pandas / YFinance| F(Macro Trend Correlation)
    
    %% Output
    F --> G(Writer Agent)
    G --> H[docs/latest_briefing.json]
    
    %% UI & API
    H -.->|GitOps Deploy| I(Frontend UI & Web Speech API)
    I <-->|REST API| J[FastAPI Server]
    J <-->|Evidence-Grounded RAG| K(QA Agent)

🚀 Core Engineering Features (Why this isn't just an LLM Wrapper)
1. Evidence-Grounded RAG (Zero-Hallucination)
The Q&A Agent does not rely on its internal weights. It operates on a strict JSON data contract. If a user asks a question, the LLM must return the answer alongside the exact string of text extracted from the source (Evidence) and a mathematical confidence score. If the evidence is missing, the system gracefully degrades and refuses to answer, preventing prompt injections and hallucinations.

2. LLM-as-a-Judge Evaluation Framework
Ranking isn't done "by eye". The system includes a quantitative evaluation framework (src/evaluation/eval_ranking.py). Against a Golden Dataset of news, the system isolates semantic scoring from deterministic sorting, achieving an NDCG@3 score of 1.0000.

3. Quantitative Market Intelligence
LLMs cannot do math. J.A.R.V.I.S. integrates a deterministic Python pipeline (yfinance, pandas) to calculate real-time asset prices, daily returns, and annualized historical volatility. The LLM only receives these exact, pre-calculated numbers to write the narrative briefing.

4. Enterprise Observability & Cost Tracking
All LLM traffic is routed through a single choke-point (LLMFallbackRouter). We implemented strict JSON structured logging that tracks:

timestamp, component, latency_ms

Exact prompt_tokens and completion_tokens via API payload

Estimated cost in USD per transaction

⚙️ Tech Stack
AI Orchestration: LangGraph, LangChain, Groq (Llama-3 70B / Qwen)

Backend API: FastAPI, Pydantic, Uvicorn

Data & Quant: Pandas, YFinance, BeautifulSoup4, SQLite

CI/CD & Deployment: GitHub Actions (Batch pipeline), Render.com (API backend), GitHub Pages (Frontend)

💻 Local Setup
Clone & Install:

Bash
git clone [https://github.com/mpozz28/jarvis-daily-briefing.git](https://github.com/mpozz28/jarvis-daily-briefing.git)
cd jarvis-daily-briefing
pip install -r requirements.txt
Environment Variables (.env):

Snippet di codice
GROQ_API_KEY=gsk_your_api_key_here
Run the Daily Pipeline (Batch):

Bash
python -m src.orchestrator
Run the Evaluation Framework:

Bash
python -m src.evaluation.eval_ranking
Start the API Server (Real-time Q&A):

Bash
python api_server.py
🛡️ Security & Scalability
Strict CORS Policy: FastAPI only accepts requests from the allowed GitHub Pages domain.

Fail-Safe Routing: The LLM router implements automatic fallback models and exponential backoff to handle 429 Rate Limits from cloud providers.

Prompt Injection Defense: Web-scraped text is explicitly framed as UNTRUSTED in the system prompt.