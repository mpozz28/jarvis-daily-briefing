# 🧠 J.A.R.V.I.S. - Evidence-Grounded AI Intelligence Platform

![Python](https://img.shields.io/badge/Python-3.12-blue)
![LangGraph](https://img.shields.io/badge/Orchestration-LangGraph-orange)

> **Elevator Pitch:** An evidence-grounded AI intelligence pipeline that aggregates multi-domain data, ranks content via a two-tower deterministic/LLM architecture, extracts cross-document knowledge graphs, and serves an interactive web UI backed by strict evidence validation and abstention protocols.

---
## 🎯 Recruiter-Facing Demo

### What can you see in under 2 minutes?

J.A.R.V.I.S. is designed to be evaluated as a **complete AI system**, not just as an LLM demo.

**1. Automated Intelligence Briefing**

Run the pipeline and watch it:

```text
Multi-source ingestion
        ↓
Deterministic ranking
        ↓
LLM semantic reranking
        ↓
Cross-document reasoning
        ↓
Market metrics
        ↓
Validated briefing
```

The output is a structured daily briefing containing the highest-ranked stories, cross-document insights and deterministic market data.

**2. Ask J.A.R.V.I.S. a Question**

Use the interactive Q&A interface to ask questions about the generated briefing.

The system:

```text
Question
  ↓
Relevant article identification
  ↓
Article / web retrieval
  ↓
Evidence extraction
  ↓
Evidence verification
  ↓
Answer or abstention
```

When sufficient evidence cannot be verified, the system abstains instead of presenting an unsupported answer as fact.

**3. Inspect the Engineering Behind the Demo**

The repository exposes the complete pipeline:

* deterministic relevance scoring;
* LLM reranking;
* multi-document relationships;
* deterministic financial calculations;
* structured Pydantic outputs;
* evidence validation;
* automated tests;
* security regression tests;
* GitHub Actions CI.

**4. Reproduce the Evaluation**

The ranking system includes an offline benchmark that compares:

```text
Input Order
     vs
Deterministic Scoring
     vs
Deterministic + LLM Reranking
```

with reproducible NDCG, Precision and Recall measurements.

### Suggested demo flow

For a technical interview, a concise walkthrough is:

```text
1. Open the live briefing
2. Show one cross-document connection
3. Ask a grounded Q&A question
4. Show the evidence / abstention behavior
5. Open the ranking agent
6. Open the evaluation results
7. Show the CI pipeline
```

This gives a recruiter or interviewer a fast view of both the **user-facing product** and the **engineering system underneath it**.

### Demo links

**Live Demo:** https://mpozz28.github.io/jarvis-daily-briefing/

**GitHub Repository:** https://github.com/mpozz28/jarvis-daily-briefing

**Architecture Decisions:** [`docs/architecture-decisions.md`](docs/architecture-decisions.md)


## 🏗️ System Architecture

J.A.R.V.I.S. implements a **Hybrid Architecture**, separating deterministic computation (Information Retrieval, Quantitative Math, Confidence Validation) from probabilistic reasoning (Semantic Reranking, Narrative Synthesis).

```mermaid
flowchart TD
    %% Ingestion
    A[Cron / GitHub Actions] --> B[Multi-Agent Data Ingestion]
    B -->|RSS / Scrape| C[(SQLite Dedup & Sanitization)]

    %% Processing Pipeline
    C --> D[Tower 1: Deterministic Scorer]
    D -->|Top 20 Filtered| E[Tower 2: LLM Semantic Reranker]
    E --> F[Multi-Document Reasoning Graph]
    F --> G["Quantitative Finance Engine<br/>Pandas / YFinance"]

    %% Output Generation
    G --> H[Executive Narrative Writer]
    H --> I[Pydantic v2 JSON Validation]
    I --> J[docs/latest_briefing.json]

    %% Serving & RAG
    J -.->|GitOps / Pages| K["Web Speech & UI Interface<br/>Safe DOM Rendering"]
    K <-->|REST API| L["Grounded QA Agent<br/>w/ Abstention Protocol"]
```

## 🚀 Core Engineering Features

### 1. Two-Tower Information Retrieval (Scoring + Reranking)
Eliminates LLM context bloat and rate limits by filtering mathematically before invoking cloud models.

- **Tower 1 (Deterministic Filter):** Evaluates time decay (*Freshness*) and source authority weights, pruning raw feeds down to the Top 20 candidates.
- **Tower 2 (Semantic Reranker):** An LLM-as-a-Judge scores macro-technological impact on the filtered subset, outputting structured scores.

### 2. Multi-Document Knowledge Reasoning
Extracts 1-to-N relationships (Edges) between distinct articles (Nodes) to identify macro-trends across disparate domains (e.g., Geopolitics → Semiconductor supply chains).

- **Hallucination Defense:** Implements strict dynamic programmatic validation to ensure all referenced `item_ids` exist in the active state database before persisting the graph.

### 3. Evidence-Grounded Q&A with Abstention
The interactive retrieval/QA system does not treat LLM self-assessment as a calibrated probability.

- **Heuristic Confidence:** Extracts an evidence quote and checks whether the generated evidence has sufficient textual overlap with retrieved source context using `difflib.SequenceMatcher`.
- **Abstention Protocol:** If the heuristic evidence score drops below 60.0%, the agent abstains ("Insufficient evidence to provide a reliable answer").

### 4. Deterministic Quantitative Layer
Financial metrics (daily return, annualized historical volatility, regime labels) are computed strictly via Pandas and injected as static strings into the LLM context, preventing generative arithmetic errors.

## 📊 Evaluation & Benchmarking

Evaluated offline on a curated 120-item relevance benchmark containing multi-domain events, hard negatives, and freshness decay. The deterministic portion of the benchmark uses a fixed `REFERENCE_TIME` parameter to calculate deterministic temporal decay independently of the live production clock.

| System | NDCG@3 | NDCG@5 | P@3 | P@5 | R@5 |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Baseline 0 (Input Order)**  | 0.9267 | 0.9400 | 1.0000 | 1.0000 | 0.0833 |
| **Baseline 1 (Deterministic Only)** | 0.9719 | 0.9764 | 1.0000 | 1.0000 | 0.0833 |
| **Current (Deterministic + LLM)** Current_LLM  | 1.0000 | 0.9851 | 1.0000 | 1.0000 | 0.0833 |

*Note: These results are specific to this curated offline benchmark and its manually assigned relevance labels. They are useful for regression testing, but they are not evidence of general ranking performance on live news. LLM reranking can also vary across model/API versions.*

## 🛡️ Security & Reliability

- **XSS Mitigation:** The frontend avoids raw HTML injection sinks for untrusted RSS/LLM/user content. Dynamic article and Q&A content is constructed with safe DOM APIs (`createElement`, `textContent`, validated URLs) rather than concatenated HTML.
- **Prompt Injection Defense:** External scraped text is treated as untrusted data and wrapped in explicit `[UNTRUSTED_WEB_CONTEXT]` boundary blocks within system prompts.
- **Fail-Fast CI/CD:** The automated GitHub Actions production pipeline enforces a strict sequence: Dependency Install → `ruff` Linter → `pytest` (Unit & Security tests) → `eval_smoke.py` (Math checks). The system only invokes expensive LLM APIs and updates the published briefing if all checks pass.

## 💻 Quick Start

### 1. Installation

```bash
git clone https://github.com/mpozz28/jarvis-daily-briefing.git
cd jarvis-daily-briefing
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Execution Commands

```bash
# Execute batch ingestion, ranking, reasoning, and JSON export:
python -m src.orchestrator

# Run offline ranking evaluation against the golden dataset:
python -m src.evaluation.eval_ranking

# Start real-time grounded Q&A API server:
python api_server.py
```

## 📘 Engineering Decisions & Limitations

**ADRs:** Deep-dives into architectural trade-offs (Why LangGraph, Why SQLite, Why safe DOM rendering, Why Heuristic Evidence Scoring) are documented in `docs/architecture-decisions.md`.

**Known Limitations:**

- **Evaluation:** The current benchmark is a static offline regression set with manual labels. A stronger research evaluation would use a larger real-world corpus, multiple annotators, temporal holdouts, and repeated runs across model versions.
- **Graph Persistence:** Multi-document relationships are ephemeral per-run; historical queries would require migrating from SQLite to a persistent Graph/Vector DB (e.g., Neo4j).
- **Web Scraping:** The current ingestion layer (BeautifulSoup) is vulnerable to anti-bot measures on JS-heavy or Cloudflare-protected SPA domains.
