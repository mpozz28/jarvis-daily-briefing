# Architectural Decision Records (ADRs) & Engineering Trade-offs

This document outlines the key architectural decisions, rationale, trade-offs, and failure modes across the J.A.R.V.I.S. pipeline.

---

## ADR 001: LangGraph State Machine vs. Autonomous Agent Loops

- **Context:** Orchestrating heterogeneous tasks (RSS parsing, scraping, ranking, deterministic finance metrics, multi-document reasoning, JSON export).
- **Decision:** Use LangGraph as a cyclic/directed state machine (`StateGraph`) with explicit nodes and state transitions.
- **Alternatives Considered:** AutoGen, CrewAI, flat sequential scripts.
- **Why LangGraph:**
  - Strict typed state contracts (`JarvisState` via `TypedDict`).
  - Deterministic execution order: ensures quantitative data is fetched before narrative drafting.
  - Predictable error boundaries and observability hooks per node.
- **Trade-offs & Failure Modes:** Less emergence than open-ended autonomous agents, but drastically reduced token consumption and zero risk of infinite execution loops.

---

## ADR 002: Deterministic Pre-Filtering + LLM Semantic Reranking (Two-Tower Architecture)

- **Context:** Scoring and prioritizing 80-120 raw news items per batch run.
- **Decision:** Implement a deterministic scoring layer (`scoring_agent.py`) evaluating $Freshness$ (temporal decay) and $Source Quality$ (domain authority weights), passing only Top 20 candidates to the LLM for semantic reranking.
- **Alternatives Considered:** Sending all raw scraped articles directly to the LLM in chunks.
- **Why Two-Tower:**
  - Token efficiency: prevents rate limits (429) on cloud inference endpoints.
  - Mitigation of "Lost in the Middle" attention degradation in long context windows.
  - Transparent scoring breakdown for observability.
- **Trade-offs & Failure Modes:** A critical macro event from an unknown blog with low source authority might be filtered out before the LLM can evaluate its semantic significance.

---

## ADR 003: Multi-Document Reasoning Graph vs. Single-Item Summarization

- **Context:** Transforming isolated news digests into cross-domain intelligence.
- **Decision:** Build an in-memory knowledge graph representation where insights represent edges connecting at least two distinct source nodes (`item_ids`), validated by concrete evidence snippets.
- **Hallucination Defense:** Programmatic validation verifying that every generated `item_id` actually exists in the ingested batch before persisting to storage.
- **Trade-offs & Failure Modes:** Requires higher context window overhead during reasoning; relationships are dynamic per batch run and not persisted into a persistent graph database (e.g., Neo4j).

---

## ADR 004: Evidence Validation & Mathematical Composite Confidence vs. Model Self-Assessment

- **Context:** Preventing hallucinated answers and fake confidence scores in user-facing interactive Q&A.
- **Decision:** Compute confidence programmatically via exact substring match verification (`difflib.SequenceMatcher.find_longest_match`) between the quoted evidence and the raw retrieved context.
- **Formula:**
  $$\text{Confidence} = 0.75 \times \text{MatchRatio} + 0.25 \times \text{SourceTrustWeight}$$
- **Abstention Protocol:** If `is_supported == False` or $\text{Confidence} < 60.0\%$, the system abstains (`"Insufficient evidence to provide a verified answer"`).
- **Trade-offs & Failure Modes:** Heuristic confidence is deterministic and reproducible, but not a calibrated posterior probability. Minor paraphrasing by the LLM can trigger false-positive abstentions.

---

## ADR 005: Deterministic Quantitative Finance Layer via Pandas/YFinance

- **Context:** Including market performance (returns, historical annualized volatility, macro regimes).
- **Decision:** Calculate all financial metrics deterministically via Pandas and inject them as static facts into the prompt.
- **Why:** LLMs fail at basic arithmetic and historical standard deviation calculations. Outsourcing calculation to Python guarantees zero-hallucination numbers.

---

## ADR 006: Frontend Security Hardening (DOMPurify vs. Custom Sanitization)

- **Context:** Rendering untrusted HTML generated from external RSS feeds and LLM outputs, exposing the system to Cross-Site Scripting (XSS).
- **Decision:** Implement `DOMPurify` to sanitize all dynamic HTML injections before mapping them to the DOM via `innerHTML`. Replaced static injections with safe `textContent` API.
- **Alternatives Considered:** Custom Regex cleaning, rewriting the frontend in React/Vue (which auto-escapes by default).
- **Why DOMPurify:** Standard industry solution for vanilla JS environments. Prevents prompt injection payloads from executing in the user's browser without requiring a heavy frontend framework rewrite.
- **Trade-offs:** Adds a lightweight external dependency to the frontend, but guarantees enterprise-level XSS mitigation.

---

## ADR 007: Information Retrieval Evaluation (Offline Golden Dataset)

- **Context:** Proving the efficacy of the Two-Tower ranking architecture over a basic heuristic filter.
- **Decision:** Built a static 120-item Golden Dataset containing ground-truth relevances, hard negatives, and outdated news. Evaluated using strict IR metrics (`NDCG@3`, `Precision@5`, `Recall@5`).
- **Alternatives Considered:** LLM-as-a-judge (subjective and uncalibrated) or A/B testing (requires heavy user traffic).
- **Why Offline NDCG:** Provides a mathematical, reproducible baseline. Proves that the LLM Reranker successfully optimizes the top percentile ordering compared to the deterministic baseline.
- **Trade-offs:** The dataset is static and requires manual updates to reflect changing macro-trends, unlike an online continuous evaluation system.

---

## ADR 008: Unified CI/CD and Data Pipeline (Fail-Fast Deployment)

- **Context:** Running the daily production briefing via GitHub Actions cron job.
- **Decision:** Integrated unit testing, security regression tests (`pytest`), syntax checking (`ruff`), and a mathematical smoke test (`eval_smoke.py`) directly into the production deployment pipeline.
- **Why:** Enforces a "Fail-Fast" architecture. If a commit breaks the logic, the pipeline terminates *before* invoking expensive LLM APIs and *before* pushing a corrupted JSON payload to the live site.
- **Trade-offs:** Slightly increases the execution time of the daily cron job, but completely eliminates the risk of deploying broken data to production.