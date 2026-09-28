import os

# General Parameters and Paths
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
DB_PATH = os.path.join(DATA_DIR, "jarvis_memory.db")

# Ensure data directory exists
os.makedirs(DATA_DIR, exist_ok=True)

# Scientific Research Feeds (ArXiv Papers)
RESEARCH_FEEDS = {
    "ArXiv_AI": "http://export.arxiv.org/rss/cs.AI",
    "ArXiv_ML": "http://export.arxiv.org/rss/cs.LG",
}

# Financial Tickers to monitor (yfinance)
MARKET_TICKERS = ["AAPL", "MSFT", "NVDA", "GOOGL", "META", "TSLA", "BTC-USD", "^GSPC"]

# Financial anomaly threshold (0.03 = flag if a stock moves +/- 3% compared to previous close)
MARKET_VOLATILITY_THRESHOLD = 0.03


# ---------------------------------------------------------------------------
# LLM configuration
# ---------------------------------------------------------------------------
# Keep model selection in one place so routing, agents, observability and tests
# cannot silently drift apart.
LLM_DEFAULT_MODEL = os.getenv(
    "JARVIS_LLM_DEFAULT_MODEL",
    "openai/gpt-oss-120b",
)

_fallback_models_raw = os.getenv(
    "JARVIS_LLM_FALLBACK_MODELS",
    "openai/gpt-oss-20b,qwen/qwen3.8-27b,openai/gpt-oss-safeguard-20b",
)
LLM_FALLBACK_MODELS = [
    model.strip() for model in _fallback_models_raw.split(",") if model.strip()
]

LLM_MODEL_POOL = [LLM_DEFAULT_MODEL] + [
    model for model in LLM_FALLBACK_MODELS if model != LLM_DEFAULT_MODEL
]


# Groq on-demand pricing, USD per 1M tokens.
# Source: Groq model documentation, verified 2026-09-20.
GROQ_MODEL_PRICING_USD_PER_1M = {
    "openai/gpt-oss-20b": {"input": 0.075, "output": 0.30},
    "openai/gpt-oss-120b": {"input": 0.15, "output": 0.60},
    "qwen/qwen3.8-27b": {"input": 0.80, "output": 4.00},
    "openai/gpt-oss-safeguard-20b": {"input": 0.075, "output": 0.30},
}
