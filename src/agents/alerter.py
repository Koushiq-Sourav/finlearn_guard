# CONTRIBUTION: Saves threats, bumps risk, broadcasts live with 5-step trace.
"""Alerter: persist the threat, bump employee risk, broadcast live.

SECTIONS:
  §1 DETECT    - rules score + AI verdict (detector)
  §2 SAVE      - persist event, prefer detected kind (7-kind taxonomy)
  §3 RISK      - phishing verdict bumps employee risk
  §4 BROADCAST - push live alert to all browsers + 5-step pipeline trace
"""
import time

from src.agents.detector import detect
from src.api.ws import broadcast
from src.storage.database import list_threats, save_threat, set_risk


async def handle_threat(title: str, kind: str = "phishing", body: str = "", employee_id: str = "") -> dict:
    t0 = time.perf_counter()
    # STEP 1 - DETECT: rules score + AI verdict
    result = detect(title, body)
    t1 = time.perf_counter()
    # STEP 2 - SAVE: persist event, prefer detected kind (7-kind taxonomy).
    # Keep explicit sender kinds like "network" (endpoint agent bursts) as-is.
    req_kind = (kind or "phishing").lower()
    det_kind = str(result.get("kind") or "phishing").lower()
    if req_kind in ("network", "support"):
        final_kind = req_kind
    elif det_kind in ("phishing", "otp", "bec", "sqli", "xss", "malware"):
        final_kind = det_kind
    else:
        final_kind = req_kind
    if final_kind == "safe" and req_kind not in ("safe", "phishing"):
        final_kind = req_kind
    # safe stays safe (honest feed); do NOT force to phishing.
    event = save_threat(title=title, kind=final_kind, severity=result["severity"])
    save_ms = round((time.perf_counter() - t1) * 1000, 1)
    # STEP 3 - RISK: phishing verdict bumps the employee's risk level
    risk_action = "no change"
    if employee_id and result["verdict"] == "phishing":
        new_risk = "high" if result["severity"] == "high" else "medium"
        set_risk(employee_id, new_risk)
        risk_action = f"{employee_id} -> {new_risk}"
    t2 = time.perf_counter()
    # STEP 4 - BROADCAST: push live alert to all open browsers
    await broadcast(
        {
            "type": "alert",
            "title": title,
            "severity": result["severity"],
            "verdict": result["verdict"],
            "kind": final_kind,
            "reason": result["reason"],
        }
    )
    broadcast_ms = round((time.perf_counter() - t2) * 1000, 1)
    total_ms = round((time.perf_counter() - t0) * 1000, 1)
    # PIPELINE TRACE (drives dashboard inspector: 5 steps, each with ms).
    pipeline = [
        {"step": 1, "name": "Received", "detail": f"{title[:80]} | kind={final_kind} | body {len(body or '')} chars", "ms": 0.0},
        {"step": 2, "name": "Rules screener", "detail": f"signals={', '.join(result.get('signals', [])) or 'none'} | score={result.get('score', 0)}", "ms": result.get("screen_ms", 0.0)},
        {"step": 3, "name": "AI verdict", "detail": f"{result.get('verdict', '?')}/{result.get('severity', '?')} — {result.get('reason', '')[:100]}", "ms": result.get("llm_ms", 0.0)},
        {"step": 4, "name": "Handling", "detail": f"saved id={event.get('id', '?')} | risk {risk_action} | live broadcast sent", "ms": round(save_ms + broadcast_ms, 1)},
        {"step": 5, "name": "Done", "detail": f"total {total_ms}ms — see guide in Support", "ms": total_ms},
    ]
    return {"event": event, **result, "recent": list_threats(limit=5), "pipeline": pipeline, "total_ms": total_ms}
