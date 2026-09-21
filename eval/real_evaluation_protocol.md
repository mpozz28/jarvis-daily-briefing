# Real-News Evaluation Protocol

## Objective

Measure whether J.A.R.V.I.S. ordering improves against a frozen relevance-labelled news snapshot, without treating a model-generated label as ground truth.

## Dataset

- RSS snapshot collected by `src/evaluation/collect_real_corpus.py`.
- Six topical areas are represented where available.
- The collector creates a temporal `dev/test` split.
- Generated article data stays outside Git by default because it is a point-in-time evaluation artifact.

## Annotation

1. `prepare_annotation_queue.py` creates the annotation queue and selects an independent double-annotation subset.
2. `llm_annotation_assist.py` may generate non-gold suggestions and rationales.
3. `export_annotation_sheet.py` creates an Excel-compatible CSV.
4. Annotators fill `annotator_a_score` and, where required, `annotator_b_score`.
5. Disagreements in the double-annotation subset require adjudication.
6. `finalize_gold_dataset.py` creates the frozen gold dataset.

LLM suggestions are assistance only. They must never silently populate `expected_relevance`.

## Scoring

Relevance is a 0-100 ordinal score. The default binary relevance threshold is 50.

Primary metrics:
- NDCG@3, @5, @10 for graded ranking quality.
- Precision@K and Recall@K for thresholded relevance.
- MRR@K for the position of the first relevant item.
- Average Precision@K for ranking quality across multiple relevant items.

## Systems

- Input order: source-corpus order.
- Deterministic: J.A.R.V.I.S. freshness + source-quality ranking.
- Deterministic + LLM: deterministic top-candidate filtering followed by semantic reranking.

## Temporal evaluation

Run `--split test` only after gold labels are frozen. The evaluator uses an explicit `--reference-time` when supplied; otherwise it derives the reference time from the newest article in the selected snapshot.

Do not tune scoring weights, prompts or thresholds on the test split.

## Reporting

Report the dataset version, split, annotation protocol, reference time, model identifier, token/cost telemetry and all metrics. Treat a single snapshot as evidence for regression testing, not as proof of generalization to all future news.