# J.A.R.V.I.S. Annotation Workflow

## Freeze the collection first
Treat `real_corpus_unannotated.json` as a collection snapshot. A later collection becomes a new dataset version.

## Create the annotation queue
Run:

    python -m src.evaluation.prepare_annotation_queue --double-fraction 0.20 --seed 42

Outputs:
- `eval/annotation_queue.json`
- `eval/double_annotation_sample.json`
- `eval/annotation_manifest.json`

The queue is randomized with a fixed seed, so the same corpus produces the same assignment.

## Annotate
For every record fill `annotator_a_id`, `annotator_a_score` from 0 to 100 and `annotator_a_notes`.
For double-annotation records, a second person independently fills the B fields.
Do not expose model rankings to annotators before gold scores are assigned.

## Adjudicate disagreements
When two scores differ materially, record the reasoning in `adjudication_notes` and fill `adjudicated_score`. Do not silently average scores or change labels to improve a metric.

## Gold dataset
After annotation, create a frozen gold dataset using the adjudicated score when present; otherwise use the accepted single-annotator score. Keep the queue as provenance.

## Test set
The `test` split is a temporal holdout and must remain untouched while prompt wording, thresholds, source weights and model choices are refined.

## Dataset versioning
Recommended names: `real_corpus_v1_unannotated.json`, `annotation_queue_v1.json`, `gold_dataset_v1.json`.
