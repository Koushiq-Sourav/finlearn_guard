# CONTRIBUTION: Decides 7-kind threat via rules + AI with safety locks.
"""Detector: rules screener first, LLM verdict via OpenRouter gateway.

SECTIONS:
  §1 PROMPT - system instructions (detector.txt: 7 kinds)
  §2 DETECT  - STEP 1 rules -> STEP 2 AI -> STEP 3 safety -> STEP 4 medium lock

No dummy fallbacks: if the key is missing, generate() raises a clear
error which is surfaced as verdict=error so the owner knows to set it.
"""
import json
import time
from pathlib import Path

from src.detection.rules import screen
from src.llm.client import generate

# ---------- §1 PROMPT: kind-aware screener instructions ----------
_PROMPT = (Path(__file__).parent.parent / "llm" / "prompts" / "detector.txt").read_text()


# ---------- §2 DETECT: rules -> AI -> safety -> medium lock ----------
def detect(title: str, body: str = "") -> dict:
    text = f"{title}\n{body}"
    # STEP 1 - RULES (offline, instant): danger words -> score 0..1 + signals
    t0 = time.perf_counter()
    rules = screen(text)
    screen_ms = round((time.perf_counter() - t0) * 1000, 1)
    # STEP 2 - AI VERDICT (online, needs key): phishing/safe + severity + reason
    t1 = time.perf_counter()
    try:
        raw = generate(f"Message:\n{text}", system=_PROMPT)
        llm_ms = round((time.perf_counter() - t1) * 1000, 1)
        start, end = raw.find("{"), raw.rfind("}")
        llm = json.loads(raw[start : end + 1]) if start >= 0 and end > start else {}
        llm_ok = True
    except Exception as exc:
        llm_ms = round((time.perf_counter() - t1) * 1000, 1)
        return {
            "verdict": "error",
            "severity": "medium",
            "kind": "phishing",
            "reason": str(exc)[:120],
            "score": rules["score"],
            "signals": rules["signals"],
            "screen_ms": screen_ms,
            "llm_ms": llm_ms,
            "llm_ok": False,
        }
    verdict = llm.get("verdict", "safe")
    severity = llm.get("severity", "medium")
    kind = str(llm.get("kind", "phishing")).lower() or "phishing"
    if kind not in ("phishing", "otp", "bec", "sqli", "xss", "malware", "safe"):
        kind = "phishing" if verdict == "phishing" else "safe"
    # STEP 3 - SAFETY OVERRIDE: score >= 0.6 is NEVER "safe", even if AI says so
    if rules["score"] >= 0.6 and verdict == "safe":
        verdict, severity = "phishing", "high"
        if kind == "safe":
            kind = "phishing"
    # STEP 4 - MEDIUM STABILIZER (demo): mild lures must show medium, not flip high/low.
    # High needs proof: score > 0.30 OR critical signal (credentials/urgency/link/account/sqli/xss).
    # Mild score 0.15-0.30 marked safe by AI -> lift to phishing/medium.
    # sqli/xss signals are always critical -> they stay HIGH.
    _CRIT = ("password", "otp", "urgent", "http", "verify", "account", "suspend",
             "union", "select", "drop", "insert", "update", "delete", "1=1", "--",
             "script", "javascript", "onerror", "onload", "alert", "cookie", "<img",
             "malware", "ransomware", ".exe", ".apk", "bit.ly", "qr", "gift",
             "invoice", "wire", "ceo", "voicemail", "whatsapp")
    _sigs = " ".join(rules["signals"]).lower()
    _has_crit = any(c in _sigs for c in _CRIT)
    if kind in ("sqli", "xss", "malware"):
        verdict = "phishing"
        if severity != "high":
            severity = "high"
    if verdict == "phishing" and severity == "high" and rules["score"] <= 0.30 and not _has_crit:
        severity = "medium"
    if verdict == "safe" and 0.15 <= rules["score"] <= 0.59:
        verdict, severity = "phishing", "medium"
        if kind == "safe":
            kind = "phishing"
    return {
        "verdict": verdict,
        "severity": severity,
        "kind": kind,
        "reason": llm.get("reason", "")[:120],
        "score": rules["score"],
        "signals": rules["signals"],
        "screen_ms": screen_ms,
        "llm_ms": llm_ms,
        "llm_ok": llm_ok,
    }
