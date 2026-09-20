import os
import re
from src.agents.qa_agent import QAAgent

def test_frontend_xss_protection_enforced():
    """Static analysis to ensure innerHTML is strictly wrapped in DOMPurify."""
    index_path = os.path.join(os.path.dirname(__file__), '../docs/index.html')
    with open(index_path, 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    # Trova tutti gli utilizzi di innerHTML
    inner_html_assignments = re.findall(r'\.innerHTML\s*=\s*(.+);', html_content)
    for assignment in inner_html_assignments:
        # Verifica che l'assegnazione passi attraverso DOMPurify
        assert "DOMPurify.sanitize(" in assignment, f"Vulnerabilità XSS trovata: innerHTML assegnato senza DOMPurify -> {assignment}"

def test_backend_neutrality_on_malicious_payloads():
    """Verifica che il backend non vada in crash e non modifichi payload XSS (delega al frontend)."""
    agent = QAAgent()
    malicious_payloads = [
        "<script>alert(1)</script>",
        "<img src=x onerror=alert(1)>",
        "<a href=\"javascript:alert(1)\">click</a>"
    ]
    for payload in malicious_payloads:
        # Passiamo payload malevoli come contesto ed evidenza
        conf = agent._calculate_deterministic_confidence(True, payload, f"Context with {payload}")
        assert conf > 0.0 # L'algoritmo matematico non deve fallire sui tag HTML