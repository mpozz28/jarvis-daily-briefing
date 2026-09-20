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
