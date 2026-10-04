# CONTRIBUTION: Proves home, health, and employees all answer 200.
"""SMOKE TEST: home page renders + health + employees API all answer 200."""
from fastapi.testclient import TestClient

from src.main import app


def test_home_and_api():
    with TestClient(app) as c:
        r = c.get("/")
        assert r.status_code == 200, r.text
        assert "FinLearn Guard" in r.text
        assert "Koushiq" in r.text
        h = c.get("/health")
        assert h.status_code == 200 and h.json()["ok"] is True
        e = c.get("/api/employees")
        assert e.status_code == 200
        assert len(e.json()["employees"]) >= 3
