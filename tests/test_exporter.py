import os
import json
import pytest
from src.export.json_exporter import JsonExporter

@pytest.fixture
def temp_exporter(tmpdir):
    # tmpdir è una variabile magica di pytest che crea una cartella temporanea sicura
    return JsonExporter(base_dir=str(tmpdir))

def test_valid_export_creates_files(temp_exporter):
    """Verifica che il modulo JsonExporter generi correttamente i file senza crash."""
    
    # Passiamo dati minimali ma validi
    news = [
        {"id": "1", "title": "Test 1", "area": "TECH", "source": "ArXiv", "url": "http://", "summary": "Desc", "published": "2026-09-20T00:00:00Z"}
    ]
    
    # Insight vuoto per semplicità, l'importante è che accetti le liste
    insights = []
    narrative = "Good morning, Sir."

    # Eseguiamo l'esportazione
    success = temp_exporter.export(news, insights, narrative)

    # Verifiche di base: la funzione non è crashata e ha restituito True
    assert success is True
    
    # I file sono stati creati fisicamente nel sistema
    assert os.path.exists(temp_exporter.latest_file)
    
    # Il file si può leggere
    with open(temp_exporter.latest_file, "r", encoding="utf-8") as f:
        data = json.load(f)
        assert "domains" in data
        assert "narrative_briefing" in data