from datetime import datetime, timezone

from src.evaluation.eval_real_news import parse_reference_time, validate_gold


def test_validate_gold_checks_every_record():
    dataset = [
        {"id":"a","expected_relevance":80,"published":"2026-09-21T10:00:00+00:00","title":"A","summary":"A","source":"X"},
        {"id":"b","expected_relevance":20,"published":"2026-09-21T11:00:00+00:00","title":"B","summary":"B","source":"X"},
    ]
    validate_gold(dataset)


def test_reference_time_uses_latest_published_timestamp():
    dataset = [
        {"published":"2026-09-21T10:00:00+00:00"},
        {"published":"2026-09-21T12:00:00+00:00"},
    ]
    assert parse_reference_time(dataset, None) == datetime(2026,9,21,12,0,tzinfo=timezone.utc)