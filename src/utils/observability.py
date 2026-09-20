import json
import logging
from collections import defaultdict
from datetime import datetime, timezone

from src.config import GROQ_MODEL_PRICING_USD_PER_1M


class JSONFormatter(logging.Formatter):
    """Structured JSON logging for production observability."""

    def format(self, record):
        log_record = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "component": getattr(record, "component", "system"),
            "message": record.getMessage(),
        }

        if hasattr(record, "metrics"):
            log_record["metrics"] = record.metrics

        if record.exc_info:
            log_record["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_record)


def setup_logger(name="jarvis_engine"):
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(JSONFormatter())
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        logger.propagate = False
    return logger


logger = setup_logger()


class LLMMetricsTracker:
    """Tracks LLM calls, tokens, latency and estimated cost per model."""

    def __init__(self):
        self.total_llm_calls = 0
        self.total_prompt_tokens = 0
        self.total_completion_tokens = 0
        self.total_cost = 0.0
        self.total_latency = 0.0
        self.by_model = defaultdict(
            lambda: {
                "calls": 0,
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "latency_sec": 0.0,
                "estimated_cost_usd": 0.0,
            }
        )

    def record_call(
        self,
        model: str,
        prompt_tokens: int,
        completion_tokens: int,
        latency: float,
    ) -> float:
        self.total_llm_calls += 1
        self.total_prompt_tokens += prompt_tokens
        self.total_completion_tokens += completion_tokens
        self.total_latency += latency

        pricing = GROQ_MODEL_PRICING_USD_PER_1M.get(model)
        cost = 0.0

        if pricing:
            cost = (
                prompt_tokens / 1_000_000 * pricing["input"]
                + completion_tokens / 1_000_000 * pricing["output"]
            )
            self.total_cost += cost

        model_metrics = self.by_model[model]
        model_metrics["calls"] += 1
        model_metrics["prompt_tokens"] += prompt_tokens
        model_metrics["completion_tokens"] += completion_tokens
        model_metrics["latency_sec"] += latency
        model_metrics["estimated_cost_usd"] += cost

        return cost

    def get_summary(self):
        return {
            "total_calls": self.total_llm_calls,
            "total_prompt_tokens": self.total_prompt_tokens,
            "total_completion_tokens": self.total_completion_tokens,
            "total_tokens": self.total_prompt_tokens + self.total_completion_tokens,
            "total_latency_sec": round(self.total_latency, 2),
            "estimated_cost_usd": round(self.total_cost, 6),
            "by_model": {
                model: {
                    **metrics,
                    "latency_sec": round(metrics["latency_sec"], 2),
                    "estimated_cost_usd": round(
                        metrics["estimated_cost_usd"], 6
                    ),
                }
                for model, metrics in self.by_model.items()
            },
        }


metrics_tracker = LLMMetricsTracker()
