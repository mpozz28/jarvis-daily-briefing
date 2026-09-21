import csv
import json

from src.evaluation.import_annotation_sheet import parse_optional_score


def test_parse_optional_score():
    assert parse_optional_score("80", "score") == 80
    assert parse_optional_score("", "score") is None


def test_parse_optional_score_rejects_invalid():
    try:
        parse_optional_score("101", "score")
    except ValueError as exc:
        assert "between 0 and 100" in str(exc)
    else:
        raise AssertionError("Expected ValueError")