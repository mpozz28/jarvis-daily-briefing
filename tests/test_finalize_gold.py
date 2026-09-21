import pytest

from src.evaluation.finalize_gold_dataset import build_gold, choose_gold_score


def test_single_annotation_becomes_gold_score():
    records = [{"id": "1", "double_annotation_required": False, "annotator_a_score": 81, "annotator_b_score": None, "adjudicated_score": None}]
    gold = build_gold(records, "v1")
    assert gold[0]["expected_relevance"] == 81
    assert gold[0]["gold_score_source"] == "single_annotator"


def test_equal_double_annotations_are_consensus():
    item = {"id": "1", "double_annotation_required": True, "annotator_a_score": 80, "annotator_b_score": 80, "adjudicated_score": None}
    assert choose_gold_score(item) == (80.0, "double_annotator_consensus")


def test_disagreement_requires_adjudication():
    item = {"id": "1", "double_annotation_required": True, "annotator_a_score": 80, "annotator_b_score": 60, "adjudicated_score": None}
    with pytest.raises(ValueError, match="requires adjudication"):
        choose_gold_score(item)