import yfinance as yf
import pandas as pd
import logging
from typing import Dict

logger = logging.getLogger(__name__)

def calculate_market_regime() -> Dict[str, dict]:
    """
    Calcola metriche finanziarie deterministiche (No LLM).
    Scarica i dati reali di mercato e calcola ritorni e volatilità.
    """
    logger.info("Esecuzione Market Quantitative Analysis in corso...", extra={"component": "quant_engine"})
    
    # Asset principali per il briefing (S&P 500, Nasdaq, Bitcoin, Oro)
    assets = {
        "SPY": "S&P 500", 
        "QQQ": "Nasdaq", 
        "BTC-USD": "Bitcoin",
        "GLD": "Gold"
    }
    
    metrics = {}
    
    try:
        for ticker, name in assets.items():
            # Scarichiamo gli ultimi 15 giorni per avere abbastanza dati per la volatilità
            data = yf.download(ticker, period="15d", progress=False)
            if data.empty:
                continue
            
            # Estrazione dei prezzi di chiusura (sicuro contro i nuovi formati multi-index di yfinance)
            closes = data['Close'].squeeze()
            
            # Calcoli Matematici con Pandas (Zero allucinazioni)
            latest_price = float(closes.iloc[-1])
            prev_price = float(closes.iloc[-2])
            daily_return = ((latest_price / prev_price) - 1) * 100
            
            # Calcolo della Volatilità Storica Annualizzata
            returns = closes.pct_change().dropna()
            volatility = float(returns.std() * (252 ** 0.5) * 100)
            
            # Identificazione basica del regime di mercato
            trend = "Bullish" if daily_return > 0 else "Bearish"
            if volatility > 20.0:
                trend += " (High Volatility)"
                
            metrics[ticker] = {
                "name": name,
                "latest_price_usd": round(latest_price, 2),
                "daily_return_pct": round(daily_return, 2),
                "annualized_volatility_pct": round(volatility, 2),
                "market_regime": trend
            }
            
        logger.info(f"Analisi quantitativa completata su {len(metrics)} asset.", extra={"component": "quant_engine"})
        return metrics
        
    except Exception as e:
        logger.error(f"Errore critico nel calcolo quantitativo: {e}", exc_info=True, extra={"component": "quant_engine"})
        return {}

# --- TEST LOCALE ---
if __name__ == "__main__":
    # Test per verificare che funzioni prima di collegarlo a LangGraph
    print("Test: Scaricamento dati e calcolo in corso...")
    risultati = calculate_market_regime()
    import json
    print(json.dumps(risultati, indent=2))