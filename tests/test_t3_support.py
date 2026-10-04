# CONTRIBUTION: Proves support ask returns steps plus media.
"""Tier 3 support test: ask -> diagnose -> guide (no quiz, no dummy files)."""
from fastapi.testclient import TestClient

from src.main import app


def test_support_ask_structure(monkeypatch):
    import src.agents.support as sup

    def fake_generate(prompt: str, system: str = "", timeout: int = 60) -> str:
        return (
            '{"problem": "Fake account phishing mail", "severity": "high", '
            '"steps": ["Do not click the link or reply", '
            '"Verify via the official site, never the mail link", '
            '"Report to IT and delete the mail"], '
            '"voice_script": "Do not click. Verify on the official site. Report to IT."}'
        )

    monkeypatch.setattr(sup, "generate", fake_generate)
    # stub media so tests stay offline
    import src.api.routes_api as api  # noqa: F401  (ensures route import)

    import src.media.video as vid
    import src.media.voice as voi

    monkeypatch.setattr(voi, "speak", lambda text: "/media/voice-test.mp3")
    monkeypatch.setattr(
        vid, "make_guide_video",
        lambda steps, title="": {"video_url": None, "slides": [{"n": 1, "text": steps[0]}], "video_error": "test-stub"},
    )

    with TestClient(app) as c:
        r = c.post("/api/support/ask", json={"question": "Verify your account urgently, click link with password", "employee_id": "E001"})
        assert r.status_code == 200, r.text
        d = r.json()
        assert d["severity"] == "high"
        assert len(d["steps"]) >= 3
        assert "quiz" not in str(d).lower()
        assert d["audio_url"] == "/media/voice-test.mp3"
        assert "slides" in d

        page = c.get("/support")
        assert page.status_code == 200 and "Diagnose" in page.text
