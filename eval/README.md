# J.A.R.V.I.S. Evaluation Protocol

This directory contains the offline ranking benchmark and the protocol used to build a research-grade relevance dataset.

## Current benchmark

`ranking_dataset.json` is a small regression fixture used to detect ranking regressions during development. It is intentionally treated as a **curated regression set**, not as evidence of general live-news ranking performance.

The evaluator uses NDCG@3/5/10, Precision@K, Recall@K, MRR@K and Average Precision@K against the ground-truth relevance set.

Deterministic benchmark:

```powershell
python -m src.evaluation.eval_ranking
```

Live LLM reranking is opt-in:

```powershell
python -m src.evaluation.eval_ranking --include-llm
```

## Real corpus collection

The repository includes `src/evaluation/collect_real_corpus.py`, a reproducible RSS collector for building an **unannotated** real-news corpus.

Run:

```powershell
python -m src.evaluation.collect_real_corpus --per-source 50 --max-items 500
```

The collector:

- pulls from multiple independent RSS sources;
- normalizes URLs and removes common tracking parameters;
- normalizes HTML/text fields;
- assigns a transparent topic hint;
- removes exact URL duplicates;
- creates a temporal `dev` / `test` split;
- writes a collection manifest;
- deliberately leaves gold relevance unassigned.

Outputs:

- `eval/real_corpus_unannotated.json`
- `eval/real_corpus_manifest.json`

The generated corpus must be manually reviewed and annotated before being used as a gold benchmark.

## Target real-world evaluation set

Target approximately 300-500 real articles across TECH, AI/ML, FINANCE, SCIENCE, WORLD and POLITICS, with multiple publication-age bands and at least six independent source domains. At least 20% should be independently double-annotated.

## Dataset format

The machine-readable annotation schema is defined in `annotation_schema.json`. The unannotated collector output is additionally described by `real_corpus_schema.json`.

Required gold fields include `id`, `title`, `summary`, `area`, `source`, `published` and `expected_relevance`.

The evaluation label should describe **content relevance**, not source prestige. Source quality is already an input to the deterministic ranker and must not be smuggled into the gold label.

## Relevance rubric

| Score | Interpretation |
|---|---|
| 90-100 | Critical: major event or development with immediate, broad significance |
| 75-89 | High: clearly important and worth prominent briefing placement |
| 50-74 | Moderate: useful context or material development, but not top-tier |
| 25-49 | Low: limited significance, narrow impact, or weak novelty |
| 0-24 | Irrelevant for the briefing, obsolete, duplicate, or otherwise unsuitable |

Annotators should judge the article itself using the same briefing objective for every item. Do not increase a score simply because the source is prestigious, the headline is sensational, or the topic is personally interesting.

## Duplicate and syndicated stories

Near-duplicates should be grouped with `duplicate_group`. Rewrites or syndicated copies of the same underlying event should not become multiple independent gold signals.

## Temporal protocol

Use a time-based holdout:

- `dev`: older articles used to refine the scoring protocol;
- `test`: a later time window kept untouched until the protocol is frozen.

Test labels should not be used to tune thresholds, prompt wording, source weights or model selection.

## Annotation quality control

At least 20% of the real corpus should be independently labeled by a second annotator. Resolve disagreements using the written rubric and document adjudication.

Do not inspect model rankings before assigning gold labels.

## Reporting

Every benchmark result should report dataset version, dataset size, relevance threshold, reference time, split, systems compared, NDCG@3/5/10, Recall@5/10, MRR@5, AP@5/10, LLM model identifier when applicable, latency, token usage and estimated cost.

Results from the current 120-item fixture must remain labeled as regression-test results. They should not be described as generalization performance.

## Current limitations

The current fixture is intentionally small and contains curated/synthetic-style examples. It is useful for regression detection but insufficient for a strong claim about real-world ranking quality.

The next research step is **data quality and annotation quality**, not further metric proliferation.
