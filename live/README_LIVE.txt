CONTRIBUTION: Local + Render + Docker runbook for going live.

FINLEARN GUARD - LIVE PACKAGE (2026-09-20)
========================================

WHAT IS LIVE (needed to run + deploy):
  src/                  FastAPI app (main.py, api/, web/, agents/, detection/, llm/, media/, storage/)
  static/               CSS + JS (style.css, app.js)
  templates/            HTML pages (dashboard, support, users, devices, base layout)
  config/settings.yaml  App name + seed employees (Koushiq/Tumpa/Rahim)
  requirements.txt      Python deps (fastapi, uvicorn, jinja2, httpx, edge-tts, moviepy, pymongo...)
  .env.example          Env template (copy to .env, NEVER commit real .env)
  data/media/           Empty folder (audio/video generate here at runtime)
  agent/                Endpoint agent for Devices pages (optional for demo, required for live network story)
  live/                 This folder: deploy + run helpers
  tests/                3 pytest files (prove it works, instructor loves this)

WHAT IS EXTRA (not needed live, moved to extra/):
  screenshots/          Old saved HTML copies of pages
  docs/rebuild-questions-archive.txt   Old planning notes
  data/media/*.mp3|*.mp4 cache         Regenerates on demand, no need to deploy
  .venv/, __pycache__/, .pytest_cache/ Local only, never deploy

WHAT IS INSTRUCTOR (to show, in instructor/):
  ARCHITECTURE.txt     System diagram + module map
  DEMO_SCRIPT.txt      3-minute click path for class demo
  API_TABLE.txt        All routes (pages + REST + WebSocket)
  REPORT_POINTS.txt    What to say: problem, solution, closed loop, tech

LOCAL LIVE (class demo, no internet needed except AI key):
  1. Double-click live\start_live.bat
     (runs: .venv python -m uvicorn src.main:app --host 127.0.0.1 --port 8000)
  2. Open http://127.0.0.1:8000/          <- main landing (analysis feed)
     Open http://127.0.0.1:8000/support    <- cyber support (voice+video guide)
  3. Env needed in .env (already set on this PC):
       OPENROUTER_API_KEY=sk-or-v1-... (real key, never share screen)
       OPENROUTER_MODEL=mistralai/ministral-8b-2512
       MONGO_URL=mongodb+srv://... (Atlas live DB)
       MONGO_DB=finlearn_guard
  4. Without key: detector/support return verdict=error (by design, no fake output).

PUBLIC LIVE (Render, free, instructor opens URL):
  1. Push this folder to GitHub (private ok). .gitignore already excludes .env/venv/media/db.
  2. Render.com -> New Web Service -> connect repo.
     Build:  pip install -r requirements.txt
     Start:  uvicorn src.main:app --host 0.0.0.0 --port $PORT
     (Or: copy live/render.yaml values by hand.)
  3. Render -> Environment, add 4 vars (copy from your local .env):
       OPENROUTER_API_KEY, OPENROUTER_MODEL,
       MONGO_URL, MONGO_DB=finlearn_guard
  4. Deploy -> you get https://finlearn-guard.onrender.com/
     Test:  /health  /  /support  /api/employees  /api/stats
  5. Docker option: live/Dockerfile builds anywhere
       docker build -f live/Dockerfile -t finlearn-guard .
       docker run -p 8000:8000 --env-file .env finlearn-guard

NOTES:
  - main.py + routes_web.py now use absolute BASE_DIR paths (deploy-safe, 2026-09-20).
  - Media dir auto-creates on boot; voice needs net (edge-tts), video needs moviepy+ffmpeg (in requirements).
  - Free Render sleeps after idle: first load ~30s, then fast. Tell instructor this.
  - NEVER paste .env key in chat/screenshots. If key leaks, revoke at openrouter.ai/keys.
