# CONTRIBUTION: All JSON doors: health, employees, threats, support, devices.
"""DATA DOORS (JSON APIs). SECTIONS:
  HEALTH    - /health (is the server alive?)
  EMPLOYEES - list + add people (/api/employees)
  THREATS   - report a threat + feed history + graphs (/api/threats, /api/stats, /api/perf)
  SUPPORT   - ask a question, get text/voice/video guide (/api/support/ask)
  DEVICES   - endpoint agent register + heartbeat + list (/api/devices/*)
"""
from fastapi import APIRouter
from pydantic import BaseModel

from src.storage.database import list_employees, list_threats, perf_summary, threat_stats

router = APIRouter()


# ---------- HEALTH: liveness probe (class demo + uptime checks) ----------
@router.get("/health")
def health():
    return {"ok": True}


# ---------- EMPLOYEES: directory doors ----------
@router.get("/api/employees")
def employees():
    return {"employees": list_employees()}


class EmployeeIn(BaseModel):
    name: str
    dept: str = ""
    id: str = ""
    risk: str = "low"

@router.post("/api/employees")
def create_employee(emp: EmployeeIn):
    from src.storage.database import add_employee

    try:
        row = add_employee(name=emp.name, dept=emp.dept, emp_id=emp.id, risk=emp.risk)
    except ValueError as exc:
        from fastapi.responses import JSONResponse

        return JSONResponse(status_code=400, content={"ok": False, "error": str(exc)})
    return {"ok": True, "employee": row}


# ---------- THREATS + GRAPHS: detection in, feed/graphs out ----------
@router.get("/api/threats")
def threats(limit: int = 10):
    return {"threats": list_threats(limit=limit)}


@router.get("/api/stats")
def stats():
    return {"per_minute": threat_stats()}


@router.get("/api/perf")
def perf():
    """Overall performance: total detections + severity/kind breakdown (drives bottom graph)."""
    return perf_summary()


class ThreatIn(BaseModel):
    title: str
    kind: str = "phishing"
    body: str = ""
    employee_id: str = ""


@router.post("/api/threats")
async def ingest(threat: ThreatIn):
    from src.agents.alerter import handle_threat

    return await handle_threat(
        title=threat.title,
        kind=threat.kind,
        body=threat.body,
        employee_id=threat.employee_id,
    )


# ---------- SUPPORT: question in, guided fix (text + voice + video) out ----------
class SupportIn(BaseModel):
    question: str
    employee_id: str = ""


@router.post("/api/support/ask")
async def support_ask(req: SupportIn):
    """Tier 3 (no quiz): ask -> auto-diagnose -> text/voice/video guide."""
    from src.agents.support import diagnose
    from src.api.ws import broadcast
    from src.storage.database import save_threat

    result = diagnose(req.question, req.employee_id)
    if result.get("verdict") != "error":
        # §SUPPORT-SAVE: store under detected kind (phishing|otp|bec|sqli|xss|malware)
        # so the perf graph counts the solution; fall back to "support" for generic Qs.
        save_kind = str(result.get("kind") or "support").lower()
        if save_kind not in ("phishing", "otp", "bec", "sqli", "xss", "malware"):
            save_kind = "support"
        event = save_threat(
            title=result.get("problem", req.question[:80]),
            kind=save_kind,
            severity=result.get("severity", "medium"),
        )
        result["event_id"] = event["id"]
        audio_url, audio_error = None, None
        try:
            from src.media.voice import speak

            audio_url = speak(result.get("voice_script", " ".join(result.get("steps", []))))
        except Exception as exc:
            audio_error = str(exc)[:150]
        from src.media.video import make_guide_video

        video = make_guide_video(result.get("steps", []), result.get("problem", "Fix guide"))
        result["audio_url"] = audio_url
        result["audio_error"] = audio_error
        result["video_url"] = video["video_url"]
        result["slides"] = video["slides"]
        result["video_error"] = video["video_error"]
        await broadcast(
            {
                "type": "support",
                "title": result.get("problem", "Support answer ready"),
                "severity": result.get("severity", "medium"),
            }
        )
    return result


# ---------- DEVICES: agent register + heartbeat + list (drives /devices page) ----------
class DeviceIn(BaseModel):
    device_id: str = ""
    employee_id: str = ""
    hostname: str = ""
    ip: str = ""
    os_info: str = ""


@router.post("/api/devices/register")
def device_register(dev: DeviceIn):
    from src.storage.database import register_device

    try:
        row = register_device(
            device_id=dev.device_id,
            employee_id=dev.employee_id,
            hostname=dev.hostname,
            ip=dev.ip,
            os_info=dev.os_info,
        )
    except ValueError as exc:
        from fastapi.responses import JSONResponse

        return JSONResponse(status_code=400, content={"ok": False, "error": str(exc)})
    return {"ok": True, "device": row}


class HeartbeatIn(BaseModel):
    device_id: str
    ip: str = ""
    conns: int = 0


@router.post("/api/devices/heartbeat")
def device_heartbeat_api(hb: HeartbeatIn):
    from src.storage.database import device_heartbeat

    try:
        row = device_heartbeat(device_id=hb.device_id, ip=hb.ip, conns=hb.conns)
    except ValueError as exc:
        from fastapi.responses import JSONResponse

        return JSONResponse(status_code=404, content={"ok": False, "error": str(exc)})
    return {"ok": True, "device": row}


@router.get("/api/devices")
def devices():
    from src.storage.database import list_devices

    return {"devices": list_devices()}
