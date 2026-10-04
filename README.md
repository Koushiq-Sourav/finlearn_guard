> **CONTRIBUTION:** Project overview: run, deploy, and test in one page.

# FinLearn Guard

Finance learning + threat-guard in one FastAPI website.
Threat in -> AI detects -> live alert to everyone -> support explains the fix by text + voice + video.

Lost? Open **`FIND_ANYTHING.md`** — every task mapped to its exact file and section.

## Run locally (easiest: double-click `live/start_live.bat`)

```bat
.venv\Scripts\python -m uvicorn src.main:app --host 127.0.0.1 --port 8000
```

Open http://127.0.0.1:8000/ and http://127.0.0.1:8000/support

## What's where

| Folder / file | Holds |
|---|---|
| `src/` | Server code: pages (`web/`), APIs (`api/`), agents (`agents/`), rules (`detection/`), AI (`llm/`), voice-video (`media/`), database (`storage/`) |
| `templates/` | Pages: `layouts/base.html` (shared topbar) + `pages/` (dashboard, support, users, devices) |
| `static/` | Looks + behavior: `css/style.css` (all styling, section-labeled), `js/app.js` (feed, inspector, graphs) |
| `tests/` | 3 automated tests (smoke, detection, support) |
| `agent/` | Endpoint agent for other PCs (`agent.py` + `install.bat`) |
| `live/` | Run + deploy: `start_live.bat`, Render/Docker files, `README_LIVE.txt` |
| `instructor/` | Demo script, architecture, API table, report points (txt) |
| `docs/` | Thesis (`THESIS.pdf`) + guide book (`GUIDE_BOOK.pdf`) with editable sources |
| `data/` | Generated voice/video cache |
| `.env` | Secrets (AI key, database URL) — never show, never push |

## Deploy (Render)

Build: `pip install -r requirements.txt`
Start: `uvicorn src.main:app --host 0.0.0.0 --port $PORT`
Env vars: `OPENROUTER_API_KEY`, `OPENROUTER_MODEL`, `MONGO_URL`, `MONGO_DB`
(see `live/render.yaml`, full guide in `live/README_LIVE.txt`)

## Test

`.venv\Scripts\python -m pytest tests -q` -> 3 passed.
