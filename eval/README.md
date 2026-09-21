# J.A.R.V.I.S. Evaluation

This directory contains the deterministic ranking regression benchmark.

## Benchmark

`ranking_dataset.json` is a curated 120-item regression fixture. It is useful for detecting changes in ranking behavior, but it is **not** a representative real-world news benchmark and should not be used to claim generalization performance.

The evaluator uses a fixed reference time for deterministic scoring.

Run the reproducible benchmark:

```bash
python -m src.evaluation.eval_ranking
```

Run the live LLM reranker explicitly:

```bash
python -m src.evaluation.eval_ranking --include-llm
```

The default run does not require an LLM API.

## Metrics

The evaluator reports:

- NDCG@3/5/10
- Precision@3/5/10
- Recall@3/5/10
- MRR@3/5/10
- Average Precision@3/5/10

The LLM comparison is opt-in because live model/API behavior can vary.

## Interpretation

Use the benchmark primarily as a **regression test**:

```
Input order
    vs.
Deterministic ranking
    vs.
Deterministic + LLM reranking
```

The dataset is intentionally kept in the repository so another developer can clone the project and reproduce the deterministic benchmark without access to external services.

For research-grade claims, the project would need a larger independently annotated corpus, temporal holdouts, repeated model runs, and explicit reporting of latency and inference cost.
