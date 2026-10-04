# CONTRIBUTION: Serves the 4 HTML pages with never-cache headers.
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path

from src.storage.database import list_employees

router = APIRouter()
BASE_DIR = Path(__file__).resolve().parent.parent.parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

# NEVER cache HTML pages: browsers must fetch fresh code every load,
# so player fixes (e.g. no-download audio/video) apply immediately.
FRESH = {"Cache-Control": "no-store"}


# ---------- PAGE 1: Dashboard (hero + live feed + inspector + employees) ----------
@router.get("/", response_class=HTMLResponse)
def dashboard(request: Request):
    employees = list_employees()
    return templates.TemplateResponse(request, "pages/dashboard.html", {"employees": employees}, headers=FRESH)


# ---------- PAGE 2: Cyber Support (ask box + Steps/Voice/Video guide) ----------
@router.get("/support", response_class=HTMLResponse)
def support_page(request: Request):
    return templates.TemplateResponse(request, "pages/support.html", {}, headers=FRESH)


# ---------- PAGE 3: All Users (full employee directory) ----------
@router.get("/users", response_class=HTMLResponse)
def users_page(request: Request):
    employees = list_employees()
    return templates.TemplateResponse(request, "pages/users.html", {"employees": employees}, headers=FRESH)


# ---------- PAGE 4: Devices (agent heartbeat status board) ----------
@router.get("/devices", response_class=HTMLResponse)
def devices_page(request: Request):
    from src.storage.database import list_devices

    return templates.TemplateResponse(request, "pages/devices.html", {"devices": list_devices()}, headers=FRESH)
