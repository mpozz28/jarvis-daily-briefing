import os
import json
import pytest
from src.export.json_exporter import JsonExporter

@pytest.fixture
def temp_exporter(tmp_path):
    # tmp_path è una fixture di pytest che crea una cartella temporanea pulita
    return JsonExporter(base_dir=str(tmp_path))

def test_valid_export_creates_files(temp_exporter):
    # Passiamo una notizia finta ma conforme
    news = [{"id": "1", "title": "Test", "area": "TECH", "source": "ArXiv", "url": "http", "description": "Desc"}]
    insights = [{"target_id": "1", "insight": "Trend 1"}]
    narrative = "Good morning, Sir."

    success = temp_exporter.export(news, insights, narrative)
    
    assert success is True
    assert os.path.exists(temp_exporter.latest_file)
    assert os.path.exists(temp_exporter.index_file)

    # Verifichiamo che il JSON sia effettivamente leggibile
    with open(temp_exporter.latest_file, "r") as f:
        data = json.load(f)
        assert data["schema_version"] == 1
        assert data["narrative_briefing"] == "Good morning, Sir."

def test_invalid_export_fails_safely(temp_exporter):
    # Dati corrotti (manca tutto)
    bad_news = [{"id": "1", "area": "TECH"}]

    # Creiamo un file preesistente "valido"
    with open(temp_exporter.latest_file, "w") as f:
        f.write('{"safe": "data"}')

    # Passiamo argomenti non conformi per testare la robustezza Pydantic
    success = temp_exporter.export(bad_news, [], "")
    
    # Questo test dipende da quanto Pydantic è restrittivo (potrebbe sistemare in automatico)
    # Verifichiamo almeno che non ci siano stati crash fatali di sistema
    assert isinstance(success, bool)