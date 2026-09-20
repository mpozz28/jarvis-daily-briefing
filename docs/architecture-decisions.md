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