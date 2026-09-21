# Relevance Annotation Guidelines

## Objective

Assign a 0-100 score answering: how prominently should this article appear in a general J.A.R.V.I.S. daily intelligence briefing?

Judge information value, not publisher quality.

## Dimensions

Consider impact, novelty, breadth and briefing value together.

## Anchor bands

- 90-100 Critical: unusually consequential, time-sensitive and broadly relevant.
- 75-89 High: clearly important and suitable for prominent placement.
- 50-74 Moderate: useful but narrower, less novel or less consequential.
- 25-49 Low: potentially interesting but below higher-value stories.
- 0-24 Irrelevant/stale/unsuitable: obsolete, duplicated, outside scope or very low-impact.

## Rules

Do not increase a score because the source is prestigious or the headline is sensational. Do not automatically penalize unknown sources. Record publication time and identify the underlying event.

Group near-duplicates with `duplicate_group` and do not treat syndicated copies as independent gold signals.

Do not inspect model rankings before assigning the gold score. Keep the gold label independent of the system being evaluated.

## Procedure

1. Read title and summary.
2. Check publication time.
3. Identify the underlying event/development.
4. Assign 0-100 using the anchor bands.
5. Assign `duplicate_group` where appropriate.
6. Record notes for borderline cases.

## Double annotation

For the double-annotated subset, compare scores and notes, identify the source of disagreement, apply the rubric and document adjudication. Never change a label solely to improve benchmark results.

Recommended metadata: `annotation_version`, `annotator_ids`, `annotated_at`, `notes`, `duplicate_group`, `split`.
