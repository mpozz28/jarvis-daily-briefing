import pytest
from src.agents import ranking_agent as ra

def mock_llm_invoke(prompt, system_prompt, preferred_model=None):
    # Simuliamo che l'LLM scelga solo la notizia con ID "2"
    return """[
        {"id": "2", "area": "TECH"}
    ]"""

def test_rank_and_filter_news(monkeypatch):
    """Testa se l'agente filtra e formatta correttamente le notizie."""
    
    # Blocchiamo le vere chiamate all'intelligenza artificiale
    monkeypatch.setattr(ra.llm_router, "invoke", mock_llm_invoke)
    
    # Blocchiamo le vere chiamate web della cache per velocizzare il test
    monkeypatch.setattr(ra.source_cache, "fetch_and_cache", lambda x: None)
    
    news_list = [
        {"id": "1", "title": "Notizia Noiosa", "description": "...", "area": "MIX"},
        {"id": "2", "title": "Notizia Importante", "description": "...", "area": "MIX"}
    ]
    
    # FORZATURA: Diciamo a Jarvis che vogliamo al massimo 1 notizia, 
    # costringendolo ad attivare l'LLM per scegliere la migliore!
    ranked = ra.rank_and_filter(news_list, max_results=1)
    
    assert isinstance(ranked, list)
    assert len(ranked) == 1
    assert ranked[0]["id"] == "2"

def test_ranking_empty_list():
    """Testa la sicurezza con liste vuote."""
    ranked = ra.rank_and_filter([])
    assert ranked == []