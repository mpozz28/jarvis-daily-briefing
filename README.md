# 🧠 J.A.R.V.I.S. - Autonomous AI Daily Briefing System

![Python](https://img.shields.io/badge/Python-3.12-blue?style=for-the-badge&logo=python)
![FastAPI](https://img.shields.io/badge/FastAPI-Backend-009688?style=for-the-badge&logo=fastapi)
![AI Agents](https://img.shields.io/badge/AI-Multi--Agent_System-FF9900?style=for-the-badge)
![Vanilla JS](https://img.shields.io/badge/Frontend-Vanilla_JS-F7DF1E?style=for-the-badge&logo=javascript)

> A fully automated, professional-grade AI assistant that curates global news, synthesizes macroeconomic trends, and delivers an interactive, voice-narrated daily briefing.

## 🚀 Overview

J.A.R.V.I.S. is not a simple wrapper around an LLM. It is a full-stack, multi-agent AI system designed to act as an executive intelligence assistant. It autonomously scrapes financial, tech, and geopolitical feeds, ranks the most critical events, identifies cross-domain correlations ("Macro-Trends"), and presents them through a meticulously designed web interface with integrated British-English Text-to-Speech (TTS).

## ✨ Core Features

- **Multi-Agent Architecture**: Dedicated Python agents handle specialized tasks (Ranking, Dot-Connecting, Narrative Writing, and Q&A).
- **Anti-Hallucination Q&A**: Users can interrupt the audio briefing to ask questions. The Q&A Agent uses Live Web Scraping (via DuckDuckGo and BeautifulSoup) to answer factually, bypassing editorial paywalls without relying on outdated LLM memory.
- **Universal Audio Engine**: Custom JavaScript audio pipeline featuring pause/resume state tracking. If J.A.R.V.I.S. is interrupted by a user query, it pauses the briefing, speaks the answer, and seamlessly resumes the main report from the exact cut-off point.
- **Automated Fallbacks**: Graceful degradation strategies handle broken RSS feeds, overly short snippets, or blocked websites.

## 🏗️ System Architecture

### Backend (Python)
- **Orchestrator**: Manages the pipeline lifecycle and Agent coordination.
- **SQLite Database**: Tracks processed news to ensure J.A.R.V.I.S. never repeats the same story twice.
- **Live Scraper**: Extracts full-text articles when RSS descriptions are intentionally truncated by publishers.
- **JSON Exporter**: Packages the processed intelligence into structured data payloads.

### Frontend (HTML/CSS/JS)
- **Annotated Manuscript UI**: A brutalist, elegant design focused on readability and intelligence.
- **Web Speech API**: Configured for `en-GB` with custom parsing rules to strip Markdown and ensure a smooth, professional voice output.

## 🛠️ Installation & Usage

1. **Clone the repository:**
   ```bash
   git clone [https://github.com/yourusername/jarvis-daily-briefing.git](https://github.com/yourusername/jarvis-daily-briefing.git)
   cd jarvis-daily-briefing

Install dependencies:

Bash
   pip install -r requirements.txt
   
Generate the Daily Intelligence:
Run the orchestrator to fetch today's data, run the AI pipeline, and generate the JSON payload:

Bash
   python -m src.orchestrator
   
Launch the Q&A API Server:

Bash
   python api_server.py
   
Open http://localhost:8000 in your browser to interact with J.A.R.V.I.S.

🧪 Testing
The system includes automated tests to validate core agent logic and JSON schema integrity:

Bash
pytest
Built with logic, Python, and a touch of British cynicism.

