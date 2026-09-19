import logging
import json
import time
from datetime import datetime
from functools import wraps

# Prezzi stimati per i modelli Groq (in dollari per 1 Milione di token)
# Questi dimostrano al recruiter che sai gestire il calcolo dei costi in produzione
GROQ_PRICING = {
    "llama3-8b-8192": {"input": 0.05, "output": 0.08},
    "llama3-70b-8192": {"input": 0.59, "output": 0.79},
    "mixtral-8x7b-32768": {"input": 0.24, "output": 0.24},
    "default": {"input": 0.10, "output": 0.10}
}

class JSONFormatter(logging.Formatter):
    """Formatta i log in JSON strutturato per sistemi di monitoraggio."""
    def format(self, record):
        log_record = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "component": getattr(record, "component", "system"),
            "message": record.getMessage(),
        }
        
        # Aggiunge metriche extra se presenti (es. latenza, token)
        if hasattr(record, "metrics"):
            log_record.update(record.metrics)
            
        if record.exc_info:
            log_record["exception"] = self.formatException(record.exc_info)
            
        return json.dumps(log_record)

def setup_logger(name="jarvis_engine"):
    logger = logging.getLogger(name)
    # Evita di duplicare i log se chiamato più volte
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(JSONFormatter())
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger

logger = setup_logger()

# --- METRICS TRACKER ---
class LLMMetricsTracker:
    """Aggrega le metriche di utilizzo dell'LLM per l'intera run."""
    def __init__(self):
        self.total_llm_calls = 0
        self.total_prompt_tokens = 0
        self.total_completion_tokens = 0
        self.total_cost = 0.0
        self.total_latency = 0.0

    def record_call(self, model: str, prompt_tokens: int, completion_tokens: int, latency: float):
        self.total_llm_calls += 1
        self.total_prompt_tokens += prompt_tokens
        self.total_completion_tokens += completion_tokens
        self.total_latency += latency
        
        pricing = GROQ_PRICING.get(model, GROQ_PRICING["default"])
        cost = ((prompt_tokens / 1_000_000) * pricing["input"]) + \
               ((completion_tokens / 1_000_000) * pricing["output"])
        
        self.total_cost += cost
        return cost
        
    def get_summary(self):
        return {
            "total_calls": self.total_llm_calls,
            "total_tokens": self.total_prompt_tokens + self.total_completion_tokens,
            "total_latency_sec": round(self.total_latency, 2),
            "estimated_cost_usd": round(self.total_cost, 6)
        }

metrics_tracker = LLMMetricsTracker()