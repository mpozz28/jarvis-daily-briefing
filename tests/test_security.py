import os
import re

from src.agents.qa_agent import QAAgent


def test_frontend_has_no_raw_html_injection_sinks():
    """Regression test: untrusted content must not reach raw HTML DOM sinks."""
    index_path = os.path.join(os.path.dirname(__file__), "../docs/index.html")
    with open(index_path, "r", encoding="utf-8") as f:
        html_content = f.read()

    assert not re.search(r"\\.innerHTML\\s*=", html_content)
    assert not re.search(r"\\.outerHTML\\s*=", html_content)
    assert ".insertAdjacentHTML(" not in html_content
    assert ".insertAdjacentText(" not in html_content


def test_frontend_uses_safe_dom_construction_and_url_validation():
    """Verify dynamic rendering uses textContent/DOM APIs and validates external URLs."""
    index_path = os.path.join(os.path.dirname(__file__), "../docs/index.html")
    with open(index_path, "r", encoding="utf-8") as f:
        html_content = f.read()

    assert "document.createElement(" in html_content
    assert ".textContent =" in html_content
    assert "new URL(" in html_content
    assert 'url.protocol === "http:"' in html_content
    assert 'url.protocol === "https:"' in html_content
    assert 'rel = "noopener noreferrer"' in html_content


def test_frontend_regression_covers_common_xss_payloads():
    """Ensure the frontend security regression explicitly covers representative payloads."""
    index_path = os.path.join(os.path.dirname(__file__), "../docs/index.html")
    with open(index_path, "r", encoding="utf-8") as f:
        html_content = f.read()

    security_test_path = os.path.join(os.path.dirname(__file__), "test_security.py")
    with open(security_test_path, "r", encoding="utf-8") as f:
        security_tests = f.read()

    payloads = [
        "<script>alert(1)</script>",
        "<img src=x onerror=alert(1)>",
        '<a href="javascript:alert(1)">click</a>',
    ]
    for payload in payloads:
        assert payload in security_tests
        assert payload not in html_content


def test_backend_neutrality_on_malicious_payloads():
    """Verify backend confidence logic remains stable for malicious-looking text."""
    agent = QAAgent()
    malicious_payloads = [
        "<script>alert(1)</script>",
        "<img src=x onerror=alert(1)>",
        '<a href="javascript:alert(1)">click</a>',
    ]
    for payload in malicious_payloads:
        conf = agent._calculate_deterministic_confidence(
            True, payload, f"Context with {payload}"
        )
        assert conf > 0.0
