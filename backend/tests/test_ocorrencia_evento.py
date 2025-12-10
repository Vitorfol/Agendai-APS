import os
import time
import requests
import pytest

from tests.insert_test_events import main as insert_test_events

BASE = os.getenv("API_BASE", "http://localhost:8000")


@pytest.fixture(scope="module", autouse=True)
def ensure_test_data():
    # Insert test events; it's safe to call multiple times (will reuse existing university)
    insert_test_events()
    # give DB a short moment to commit
    time.sleep(0.2)


def test_non_disciplina_occurrence():
    # event id 3 expected from insert_test_events
    url = f"{BASE}/api/events/3/2025-11-30"
    r = requests.get(url, timeout=5)
    assert r.status_code == 200, f"Expected 200, got {r.status_code} {r.text}"
    j = r.json()
    # shape checks
    assert j.get("local") == "Sala Teste 1"
    assert j.get("data") == "2025-11-30"
    assert j.get("hora") == "09:00:00"
    assert j.get("nome") == "Reunião de Projeto - Teste"
    assert j.get("categoria") == "Reunião"
    # dias should NOT be present for non-disciplina
    assert "dias" not in j


def test_disciplina_occurrence():
    url = f"{BASE}/api/events/4/2025-12-01"
    r = requests.get(url, timeout=5)
    assert r.status_code == 200, f"Expected 200, got {r.status_code} {r.text}"
    j = r.json()
    assert j.get("local") == "Sala Disciplina"
    assert j.get("data") == "2025-12-01"
    # hora for disciplina should be the horario string
    assert j.get("hora") == "AB"
    assert j.get("nome") == "Disciplina Teste"
    assert j.get("categoria") == "Disciplina"
    assert j.get("recorrencia") == "Semanal"
    assert "dias" in j and isinstance(j["dias"], list)
    # order expected: Segunda, Quarta, Sexta
    assert j["dias"] == ["Segunda", "Quarta", "Sexta"]
