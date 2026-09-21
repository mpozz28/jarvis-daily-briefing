from collections import Counter


def _validate_score(value, field: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{field} must be numeric")
    if not 0 <= value <= 100:
        raise ValueError(f"{field} must be between 0 and 100")
    return float(value)


def validate_queue(records: list[dict], require_complete: bool = False) -> dict:
    if not isinstance(records, list) or not records:
        raise ValueError("Annotation queue must be a non-empty list")

    ids = [str(item.get("id", "")) for item in records]
    if any(not item_id for item_id in ids):
        raise ValueError("Every annotation record requires an id")
    if len(set(ids)) != len(ids):
        raise ValueError("Annotation queue contains duplicate ids")

    double_count = 0
    complete_count = 0
    incomplete_ids = []

    for item in records:
        is_double = bool(item.get("double_annotation_required"))
        if is_double:
            double_count += 1

        a_score = item.get("annotator_a_score")
        b_score = item.get("annotator_b_score")
        adjudicated = item.get("adjudicated_score")

        if a_score is not None:
            _validate_score(a_score, "annotator_a_score")
        if b_score is not None:
            _validate_score(b_score, "annotator_b_score")
        if adjudicated is not None:
            _validate_score(adjudicated, "adjudicated_score")

        complete = a_score is not None and (not is_double or b_score is not None)
        if complete:
            complete_count += 1
        else:
            incomplete_ids.append(str(item["id"]))

    if require_complete and incomplete_ids:
        raise ValueError(
            f"Incomplete annotations: {len(incomplete_ids)} records; "
            f"first ids={incomplete_ids[:5]}"
        )

    return {
        "items": len(records),
        "double_annotation_items": double_count,
        "complete_annotation_items": complete_count,
        "incomplete_annotation_items": len(incomplete_ids),
    }


def weighted_kappa_10_bins(scores_a: list[float], scores_b: list[float]) -> float:
    if len(scores_a) != len(scores_b) or not scores_a:
        raise ValueError("Score lists must have equal non-zero length")

    bins = 10
    matrix = [[0.0 for _ in range(bins)] for _ in range(bins)]
    for a, b in zip(scores_a, scores_b):
        a_bin = min(int(float(a) // 10), 9)
        b_bin = min(int(float(b) // 10), 9)
        matrix[a_bin][b_bin] += 1

    n = float(len(scores_a))
    row = [sum(values) / n for values in matrix]
    col = [sum(matrix[i][j] for i in range(bins)) / n for j in range(bins)]
    observed = 0.0
    expected = 0.0

    for i in range(bins):
        for j in range(bins):
            weight = 1.0 - abs(i - j) / (bins - 1)
            observed += weight * matrix[i][j] / n
            expected += weight * row[i] * col[j]

    if expected == 1.0:
        return 1.0
    return (observed - expected) / (1.0 - expected)


def agreement_report(records: list[dict]) -> dict:
    paired = [
        item
        for item in records
        if item.get("double_annotation_required")
        and item.get("annotator_a_score") is not None
        and item.get("annotator_b_score") is not None
    ]
    if not paired:
        return {
            "double_annotated_items": 0,
            "exact_agreement_rate": None,
            "within_5_points_rate": None,
            "within_10_points_rate": None,
            "within_20_points_rate": None,
            "mean_absolute_difference": None,
            "weighted_kappa_10_bins": None,
        }

    diffs = [
        abs(float(item["annotator_a_score"]) - float(item["annotator_b_score"]))
        for item in paired
    ]
    a_scores = [float(item["annotator_a_score"]) for item in paired]
    b_scores = [float(item["annotator_b_score"]) for item in paired]

    return {
        "double_annotated_items": len(paired),
        "exact_agreement_rate": sum(diff == 0 for diff in diffs) / len(diffs),
        "within_5_points_rate": sum(diff <= 5 for diff in diffs) / len(diffs),
        "within_10_points_rate": sum(diff <= 10 for diff in diffs) / len(diffs),
        "within_20_points_rate": sum(diff <= 20 for diff in diffs) / len(diffs),
        "mean_absolute_difference": sum(diffs) / len(diffs),
        "weighted_kappa_10_bins": weighted_kappa_10_bins(a_scores, b_scores),
    }