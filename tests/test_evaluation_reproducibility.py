from datetime import datetime, timezone

from src.agents.scoring_agent import calculate_freshness_score


REFERENCE_TIME = datetime.fromisoformat("2026-09-20T12:00:00+00:00")


def test_freshness_is_reproducible_with_fixed_reference_time():
    published = "2026-09-20T03:00:00+00:00"
    first = calculate_freshness_score(published, reference_time=REFERENCE_TIME)
    second = calculate_freshness_score(published, reference_time=REFERENCE_TIME)
    assert first == second


def test_reference_time_is_timezone_aware():
    assert REFERENCE_TIME.tzinfo == timezone.utc


def test_different_reference_times_change_only_when_expected():
    published = "2026-09-18T12:00:00+00:00"
    old_reference = datetime.fromisoformat("2026-09-19T12:00:00+00:00")
    new_reference = datetime.fromisoformat("2026-09-20T12:00:00+00:00")

    old_score = calculate_freshness_score(published, reference_time=old_reference)
    new_score = calculate_freshness_score(published, reference_time=new_reference)

    assert old_score != new_score
