# CONTRIBUTION: Vercel serverless entrypoint (Render/local untouched).
#
# WHAT: re-exports the FastAPI `app` from src/main.py so Vercel's Python
# runtime serves the whole site (pages + REST) as one function.
# WHY a separate file: Vercel only runs files under api/ - it never sees
# src/main.py or Procfile on its own (that missing entrypoint was the
# "Internal Server Error" on every route).
# NOT covered: /ws/alerts live push + /media voice/video generation need a
# long-running server (Render) - on Vercel those routes fail by design.
"""Vercel entrypoint: exposes the FinLearn Guard ASGI app."""
from src.main import app  # noqa: F401  (Vercel looks for top-level `app`)
