# CONTRIBUTION: Wires routers, static, media, and websocket into one app.
"""FinLearn Guard server: ONE app serves pages + APIs + live alerts + media.

SECTIONS:
  IMPORTS  - page routes (web), data doors (api), live hub (ws), database
  LIFESPAN - runs once at startup: creates DB tables + seeds 3 employees
  APP      - mounts the routers + /static (CSS/JS) + /media (mp3/mp4)
  WEBSOCKET - /ws/alerts: browsers stay connected here for live feed
"""
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.websockets import WebSocket

from src.api.routes_api import router as api_router
from src.api.ws import handler as ws_handler
from src.storage.database import init_db
from src.web.routes_web import router as web_router

BASE_DIR = Path(__file__).resolve().parent.parent


# ---------- LIFESPAN: startup job (collections + seed employees) ----------
@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db(seed=True)
    yield


# ---------- APP: one server, three mounts ----------
app = FastAPI(title="FinLearn Guard")
app.include_router(api_router)    # data doors: /api/*, /health
app.include_router(web_router)    # pages: /  /support  /users  /devices
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")  # CSS + JS

# ---------- MEDIA: generated voice/video files (mp3/mp4 served here) ----------
_media = BASE_DIR / "data" / "media"
_media.mkdir(parents=True, exist_ok=True)
app.mount("/media", StaticFiles(directory=str(_media)), name="media")


# ---------- WEBSOCKET: live alert channel (dashboard LIVE pill) ----------
@app.websocket("/ws/alerts")
async def ws_alerts(ws: WebSocket):
    await ws_handler(ws)
