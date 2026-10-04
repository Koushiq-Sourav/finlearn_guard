# CONTRIBUTION: Proves threat report flows into feed and graphs.
"""T2 DETECTION TEST: POST threat -> verdict+severity -> feed list -> graphs data."""
from fastapi.testclient import TestClient

from src.main import app


def test_threat_pipeline():
    with TestClient(app) as c:
        r = c.post(
            "/api/threats",
            json={
                "title": "Team lunch Friday",
                "body": "Reminder: team lunch at the usual place.",
                "employee_id": "E001",
            },
        )
        assert r.status_code == 200, r.text
        d = r.json()
        assert "verdict" in d and "severity" in d
        lst = c.get("/api/threats?limit=5")
        assert lst.status_code == 200
        assert any("Team lunch" in t["title"] for t in lst.json()["threats"])
        st = c.get("/api/stats")
        assert st.status_code == 200 and "per_minute" in st.json()
        pf = c.get("/api/perf")
        assert pf.status_code == 200
        assert "total" in pf.json() and "by_severity" in pf.json()
