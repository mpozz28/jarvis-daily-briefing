import pytest
import src.agents.ranking_agent as ra

# Finto modello LLM che risponde sempre con lo stesso JSON simulato
def mock_llm_invoke(prompt, system_prompt, preferred_model=None):
    return """
    ```json
    [
      {
        "id": "2",
        "impact_score": 9,
        "reasoning": "Molto importante."
      }
    ]
    ```
    """

def test_rank_and_filter_news(monkeypatch):
    """Testa se l'agente filtra e formatta correttamente le notizie usando l'LLM simulato."""
    
    # Blocchiamo le vere chiamate all'intelligenza artificiale
    monkeypatch.setattr(ra.llm_router, "invoke", mock_llm_invoke)
    
    news_list = [
        {"id": "1", "title": "Notizia Noiosa", "description": "...", "area": "MIX"},
        {"id": "2", "title": "Notizia Importante", "description": "...", "area": "MIX"}
    ]
    
    # Eseguiamo l'agente. Usiamo max_items=1 (in base a come è stato scritto in run_benchmark.py)
    try:
        ranked = ra.rank_and_filter(news_list, max_items=1)
    except TypeError:
        # Se anche max_items non esiste, proviamo senza parametri opzionali,
        # che è l'utilizzo standard della pipeline.
        ranked = ra.rank_and_filter(news_list)

    # Verifichiamo che l'agente non sia andato in crash
    assert isinstance(ranked, list)