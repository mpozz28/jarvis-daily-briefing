# J.A.R.V.I.S. Evaluation Protocol

This directory contains the offline ranking benchmark and the protocol used to build a research-grade relevance dataset.

## Current benchmark

`ranking_dataset.json` is a small regression fixture used to detect ranking regressions during development. It is intentionally treated as a **curated regression set**, not as evidence of general live-news ranking performance.

The evaluator uses:

- NDCG@3, @5, @10 for graded relevance
- Precision@K for binary relevance at a configurable threshold
- Recall@K for retrieval coverage
- MRR@K for the first relevant result
- Average Precision@K against the ground-truth relevance set

The standard command is deterministic and does not call an external LLM:

```powershell
python -m src.evaluation.eval_ranking
```

The live LLM reranker is opt-in:

```powershell
python -m src.evaluation.eval_ranking --include-llm
```

## Target real-world evaluation set

The next dataset version should contain approximately 300-500 real articles sampled across multiple topic areas, source types and publication ages.

Recommended coverage:

| Dimension | Target |
|---|---|
| Articles | 300-500 |
| Areas | TECH, AI/ML, FINANCE, SCIENCE, WORLD, POLITICS |
| Age bands | 0-12h, 12-24h, 1-2d, 2-7d, >7d |
| Sources | >=6 independent domains |
| Annotation scale | 0-100 |
| Double-annotated subset | >=20% |
| Locked test set | temporal holdout |

The exact counts are targets, not hard requirements. The important property is that the sample is diverse enough to expose failure modes.

## Dataset format

The machine-readable schema is defined in `annotation_schema.json`.

Required fields for a future real corpus:

- `id`
- `title`
- `summary`
- `area`
- `source`
- `published`
- `expected_relevance`

Recommended additional fields:

- `url`
- `canonical_url`
- `duplicate_group`
- `split`
- `annotation_version`
- `annotator_ids`
- `notes`

The evaluation label should describe **content relevance**, not source prestige. Source quality is already an input to the deterministic ranker and must not be smuggled into the gold label.

## Relevance rubric

Use the following anchors when assigning `expected_relevance`:

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

When a duplicate group is present, annotate the underlying event relevance consistently and record source-specific differences only in `notes`.

## Temporal protocol

For a research-grade test set, use a time-based holdout.

A practical structure is:

- `dev`: older articles used to refine the scoring protocol
- `test`: a later time window kept untouched until the protocol is frozen

The `test` labels should not be used to tune thresholds, prompt wording, source weights or model selection.

## Annotation quality control

At least 20% of the real corpus should be independently labeled by a second annotator.

Resolve disagreements using the written rubric rather than silently averaging scores. Report the final adjudication process in the evaluation report.

For the double-annotated subset, report an agreement statistic appropriate to the selected label representation. The important goal is to demonstrate that the rubric produces reasonably consistent judgments, not to manufacture a high agreement number.

## Reporting

Every benchmark result should report:

- dataset version
- dataset size
- relevance threshold
- temporal reference time
- split used
- systems compared
- NDCG@3/5/10
- Recall@5/10
- MRR@5
- AP@5/10
- whether an external LLM was used
- LLM model identifier when applicable
- latency, token usage and estimated cost for live LLM evaluation

Results from the current 120-item fixture must be labeled as regression-test results. They should not be described as generalization performance.

## Current limitations

The current fixture is intentionally small and contains curated/synthetic-style examples. It is useful for detecting regressions but is not sufficient for a strong claim about real-world ranking quality.

The next research step is therefore **data quality and annotation quality**, not further metric proliferation.
