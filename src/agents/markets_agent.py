import concurrent.futures
import logging
import re

import feedparser
import yfinance as yf

from src.config import MARKET_TICKERS, MARKET_VOLATILITY_THRESHOLD

logger = logging.getLogger(__name__)


def fetch_markets() -> list[dict]:
    """Analyzes a basket of stock tickers and generates alerts for price anomalies."""
    market_items = []

    logger.info("Checking stock market anomalies...")
    for ticker in MARKET_TICKERS:
        try:
            stock = yf.Ticker(ticker)
            hist = stock.history(period="5d")

            if len(hist) < 2:
                continue

            close_yesterday = hist["Close"].iloc[-1]
            close_prev = hist["Close"].iloc[-2]
            pct_change = (close_yesterday - close_prev) / close_prev

            if abs(pct_change) >= MARKET_VOLATILITY_THRESHOLD:
                trend = "up" if pct_change > 0 else "down"
                sign = "+" if pct_change > 0 else ""
                market_date = hist.index[-1].strftime("%Y-%m-%d")

                market_items.append(
                    {
                        "id": f"yfinance_{ticker}_{market_date}",
                        "title": f"Abnormal movement for {ticker}: {sign}{pct_change:.2%}",
                        "summary": f"{ticker} recorded a significant movement, closing at {close_yesterday:.2f} USD ({trend} by {pct_change:.2%}).",
                        "domain": "Finance",
                        "source": "Yahoo Finance Data",
                        "url": f"https://finance.yahoo.com/quote/{ticker}",
                        "published": market_date,
                    }
                )
        except Exception as e:
            logger.error(f"Error analyzing ticker {ticker}: {e}")

    return market_items


MARKET_SOURCES = {
    "WSJ_Markets": "https://feeds.a.dj.com/rss/RSSMarketsMain.xml",
    "CNBC_Economy": "https://search.cnbc.com/rs/search/combinedcms/view.xml?profile=120000000",
    "The_Economist": "https://www.economist.com/finance-and-economics/rss.xml",
}


def get_real_date(entry: dict) -> str:
    possible_keys = [
        "published",
        "updated",
        "pubDate",
        "published_at",
        "publishedAt",
        "date",
        "created_at",
        "time_published",
        "dc:date",
    ]
    for key in possible_keys:
        val = entry.get(key)
        if val:
            return str(val)
    return ""


def _fetch_finance_source(name: str, url: str, max_per_source: int) -> list[dict]:
    results = []
    try:
        feed = feedparser.parse(url)
        for entry in feed.entries[:max_per_source]:
            desc = re.sub("<[^<]+>", "", entry.get("description", ""))
            date_str = get_real_date(entry)

            results.append(
                {
                    "id": entry.get("link", ""),
                    "source": name,
                    "domain": name,
                    "title": entry.get("title", "Untitled"),
                    "description": desc[:200] + "..." if len(desc) > 200 else desc,
                    "url": entry.get("link", ""),
                    "published": date_str,
                }
            )
    except Exception as e:
        logger.warning(f"Error fetching {name}: {e}")
    return results


def fetch_market_news(max_per_source: int = 8) -> list[dict]:
    """Orchestrates parallel fetching of financial news."""
    logger.info("Starting Finance collection (Parallel execution)...")
    market_news = []

    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = [
            executor.submit(_fetch_finance_source, name, url, max_per_source)
            for name, url in MARKET_SOURCES.items()
        ]
        for future in concurrent.futures.as_completed(futures):
            market_news.extend(future.result())

    return market_news
