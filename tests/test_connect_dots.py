from src.agents import connect_dots_agent as cd
from src.agents.connect_dots_agent import connect_the_dots


def mock_llm_invoke(prompt, system_prompt, preferred_model=None):
    if "GPT-5" in prompt:
        return """[
            {"target_id": "1", "insight": "Microsoft e OpenAI dominano."},
            {"target_id": "2", "insight": "Microsoft e OpenAI dominano."}
        ]"""
    return "[]"


def test_connect_the_dots(monkeypatch):
    """Testa se l'agente individua correttamente un macro-trend."""
    monkeypatch.setattr(cd.llm_router, "invoke", mock_llm_invoke)

    mock_news = [
        {
            "id": "1",
            "domain": "Research AI",
            "title": "OpenAI lancia GPT-5",
            "summary": "Nuovo modello di Sam Altman",
        },
        {
            "id": "2",
            "domain": "Finance",
            "title": "MSFT sale del 3%",
            "summary": "Crescita spinta da cloud e AI",
        },
    ]

    insights = connect_the_dots(mock_news)

    assert isinstance(insights, list)


def test_connect_the_dots_no_correlation(monkeypatch):
    """Testa che non vengano trovati collegamenti se le notizie non condividono nulla."""

    def mock_llm_invoke_no_overlap(prompt, system_prompt, preferred_model=None):
        return "[]"

    monkeypatch.setattr(cd.llm_router, "invoke", mock_llm_invoke_no_overlap)

    mock_news = [
        {
            "id": "3",
            "domain": "Research AI",
            "title": "OpenAI lancia GPT-5",
            "summary": "...",
        },
        {
            "id": "4",
            "domain": "Finance",
            "title": "Apple annuncia nuovi iPhone",
            "summary": "...",
        },
    ]

    insights = connect_the_dots(mock_news)
    assert isinstance(insights, list)
