# J.A.R.V.I.S. Evaluation Protocol

This directory contains the offline ranking regression benchmark and the protocol for building a research-grade real-news relevance dataset.

## 1. Development regression benchmark

`ranking_dataset.json` is a curated regression fixture used to detect ranking regressions. It is not evidence of general live-news ranking performance.

Run:

    python -m src.evaluation.eval_ranking

Live LLM reranking:

    python -m src.evaluation.eval_ranking --include-llm

Metrics: NDCG@3/5/10, Precision@K, Recall@K, MRR@K and Average Precision@K.

## 2. Real corpus collection

`src/evaluation/collect_real_corpus.py` builds an unannotated real-news corpus from multiple RSS sources.

Recommended collection:

    python -m src.evaluation.collect_real_corpus --per-source 50 --max-items 450 --max-per-source-output 30 --test-days 1

The collector normalizes URLs, removes exact duplicates, limits per-source representation, assigns transparent topic areas, creates a temporal dev/test split, and never assigns gold relevance automatically.

Generated collection artifacts are intentionally ignored by Git.

## 3. Annotation queue

Create a reproducible randomized queue with a stratified 20% double-annotation sample:

    python -m src.evaluation.prepare_annotation_queue --double-fraction 0.20 --seed 42

Current corpus snapshot: 366 records, 73 selected for independent second annotation.

Do not expose model rankings to annotators before relevance scores are assigned.

## 4. Relevance rubric

| Score | Interpretation |
|---|---|
| 90-100 | Critical: major development with immediate, broad briefing significance |
| 75-89 | High: clearly important and suitable for prominent briefing placement |
| 50-74 | Moderate: useful material development or context, but not top-tier |
| 25-49 | Low: limited significance, narrow impact, or weak novelty |
| 0-24 | Minimal: little briefing value, obsolete, duplicate, or otherwise unsuitable |

Judge content relevance to the briefing objective, not source prestige. Source quality is already an input to the deterministic ranker and must not be smuggled into the gold label.

## 5. Annotation validation and agreement

Before finalization:

    python -m src.evaluation.validate_annotations

After annotation is complete:

    python -m src.evaluation.validate_annotations --require-complete

The report includes completeness, double-annotation count, exact agreement, within-5/10/20-point agreement, mean absolute score difference and weighted kappa over ten relevance bins.

Disagreements must be adjudicated and recorded; they are never silently averaged.


## 5a. Optional LLM-assisted annotation

LLM assistance can reduce annotation effort, but its output is explicitly **non-gold**:

    python -m src.evaluation.llm_annotation_assist --model-a openai/gpt-oss-120b --model-b qwen/qwen3.8-27b

Then export an Excel-compatible sheet:

    python -m src.evaluation.export_annotation_sheet

Annotators review the article and enter human scores independently. LLM suggestions and rationales remain visible as optional assistance, not as the final label.

After review, import the completed sheet:

    python -m src.evaluation.import_annotation_sheet

The recommended portfolio wording is **"LLM-assisted annotation with independent double-annotation and documented adjudication"**, not "human gold" unless the relevant labels were actually assigned/reviewed by humans.

## 6. Freeze the gold dataset

Once annotation and adjudication are complete:

    python -m src.evaluation.finalize_gold_dataset --version real_news_v1

This creates `eval/gold_dataset_v1.json`. A double-annotated disagreement without an explicit adjudicated score causes finalization to fail.

## 7. Temporal evaluation protocol

The dev split is available for refining thresholds, prompts, source weights and model configuration. The test split is a later temporal holdout and must remain untouched until the protocol is frozen.

Do not tune on test labels.

## 8. Reporting requirements

Real benchmark reports should include dataset version, collection timestamp, article count, source domains, dev/test split, topic distribution, annotation coverage, double-annotation agreement, relevance threshold, fixed reference time, NDCG@3/5/10, Recall@5/10, MRR@5, AP@5/10, LLM model identifier, latency, token usage and estimated cost.

The current 120-item fixture remains explicitly a regression benchmark, not generalization performance.

## 9. Research limitations

The real corpus is a manually annotated benchmark built from RSS metadata. It is not a random sample of all global news; topic and source distributions describe this collection snapshot only.

The next scientific bottleneck is annotation quality and dataset validity, not adding more ranking metrics.
