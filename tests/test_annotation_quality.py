import pytest

from src.evaluation.annotation_quality import agreement_report, validate_queue, weighted_kappa_10_bins


def record(item_id, a, b=None, double=False):
    return {
        "id": item_id,
        "double_annotation_required": double,
        "annotator_a_score": a,
        "annotator_b_score": b,
        "adjudicated_score": None,
    }


def test_validate_queue_counts_completion():
    report = validate_queue([record("1", 80), record("2", 70, 75, True)])
    assert report["items"] == 2
    assert report["double_annotation_items"] == 1
    assert report["complete_annotation_items"] == 2


def test_weighted_kappa_is_perfect_for_identical_scores():
    assert weighted_kappa_10_bins([10, 50, 90], [10, 50, 90]) == pytest.approx(1.0)


def test_agreement_report_measures_score_distance():
    report = agreement_report([record("1", 80, 82, True), record("2", 20, 50, True)])
    assert report["double_annotated_items"] == 2
    assert report["within_5_points_rate"] == 0.5
    assert report["within_10_points_rate"] == 0.5
    assert report["mean_absolute_difference"] == 16.0