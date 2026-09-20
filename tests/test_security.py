from src.agents.qa_agent import QAAgent

def test_xss_payload_in_evidence_is_handled():
    """Verifica che payload XSS vengano estratti e non eseguiti, demandando la sanitizzazione al frontend."""
    agent = QAAgent()
    
    malicious_text = "<script>alert('XSS')</script> This is the answer."
    evidence = "<script>alert('XSS')</script>"
    
    # Passiamo (is_supported=True, evidence, source_text)
    conf = agent._calculate_deterministic_confidence(True, evidence, malicious_text)
    
    # La confidenza sarà calcolata correttamente tramite SequenceMatcher. 
    # Nessun crash Python. La prevenzione XSS reale è poi garantita dal frontend.
    assert conf > 0