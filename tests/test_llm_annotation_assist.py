import pytest

from src.evaluation.llm_annotation_assist import parse_response


def test_parse_response_accepts_valid_annotations():
    parsed = parse_response(
        '[{"id":"a","score":82,"rationale":"High impact","flags":["high_impact"]}]',
        {"a"},
    )
    assert parsed["a"]["score"] == 82.0


def test_parse_response_rejects_missing_ids():
    with pytest.raises(ValueError, match="Missing annotations"):
        parse_response('[{"id":"a","score":82}]', {"a", "b"})


def test_parse_response_rejects_out_of_range_score():
    with pytest.raises(ValueError, match="Invalid score"):
        parse_response('[{"id":"a","score":101}]', {"a"})