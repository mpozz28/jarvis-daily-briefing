from src.utils.observability import LLMMetricsTracker


def test_metrics_are_tracked_per_model():
    tracker = LLMMetricsTracker()

    first_cost = tracker.record_call(
        "openai/gpt-oss-120b", 1_000_000, 1_000_000, 1.5
    )
    second_cost = tracker.record_call(
        "openai/gpt-oss-20b", 500_000, 250_000, 0.5
    )

    summary = tracker.get_summary()

    assert summary["total_calls"] == 2
    assert summary["total_prompt_tokens"] == 1_500_000
    assert summary["total_completion_tokens"] == 1_250_000
    assert summary["total_tokens"] == 2_750_000
    assert summary["total_latency_sec"] == 2.0

    assert "openai/gpt-oss-120b" in summary["by_model"]
    assert "openai/gpt-oss-20b" in summary["by_model"]
    assert summary["by_model"]["openai/gpt-oss-120b"]["calls"] == 1
    assert summary["by_model"]["openai/gpt-oss-20b"]["calls"] == 1
    assert first_cost > 0
    assert second_cost > 0


def test_unknown_model_cost_is_not_fabricated():
    tracker = LLMMetricsTracker()

    cost = tracker.record_call("unknown/model", 1000, 1000, 0.1)
    summary = tracker.get_summary()

    assert cost == 0.0
    assert summary["estimated_cost_usd"] == 0.0
    assert summary["by_model"]["unknown/model"]["calls"] == 1
