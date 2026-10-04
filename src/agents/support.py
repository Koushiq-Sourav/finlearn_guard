# CONTRIBUTION: Turns any question into kind-matched fix steps plus voice script.
"""Tier 3 SUPPORT (no quiz): user asks -> auto-diagnose -> guide.

SECTIONS:
  §1 PROMPT   - OpenRouter system prompt (support.txt)
  §2 SCRUB    - deflect ban + self/dev pools (7 kinds)
  §3 DIAGNOSE - question -> screen + detect -> LLM guide -> steps/voice
"""
import json
from pathlib import Path

from src.agents.detector import detect
from src.detection.rules import screen
from src.llm.client import generate

# ---------- §1 PROMPT: system instructions for the guide writer ----------
_PROMPT = (Path(__file__).parent.parent / "llm" / "prompts" / "support.txt").read_text()


# ---------- §2 SCRUB: deflect ban + pools per attack family ----------
# DEFLECTION BAN (owner order): the guide must teach SELF-handling. The LLM
# sometimes still slips in "contact IT / report to admin" steps, so we scrub
# deterministically here - no LLM obedience required.
_DEFLECT_KEYS = (
    "it team", "helpdesk", "help desk", "administrator",
    "contact support", "call support", "contact bank",
    "report phishing", "report to", "to it", "tell your admin", "ask your admin",
)
_SELF_POOL = [
    "Delete the suspicious message right away",
    "Block the sender so it cannot reach you again",
    "Open the official website or app yourself and check there",
    "Change your password on the real site only",
    "Turn on two-factor authentication for extra safety",
]
_DEV_SQLI_POOL = [
    "Rewrite the query with parameters / prepared statements, never concat input",
    "Validate input on server with allowlist, reject quotes and comment marks",
    "Give the app DB user least privilege, never admin rights",
    "Show a generic error page, never raw database errors",
]
_DEV_XSS_POOL = [
    "Escape all user input before rendering it on the page",
    "Use textContent instead of innerHTML for user data",
    "Strip script tags and onerror / onload handlers from input",
    "Set a Content-Security-Policy header to block inline scripts",
]
_OTP_POOL = [
    "Never share any OTP with anyone, not even bank staff",
    "Hang up and call back on the official number yourself",
    "Block the caller number and delete the message",
    "Turn on two-factor authentication in the real app",
]
_BEC_POOL = [
    "Verify any payment request by a second channel (call/visit)",
    "Check the sender domain letter by letter for spoofing",
    "Confirm with finance lead in person before any wire",
    "Never wire money from mail instructions alone",
]
_MAL_POOL = [
    "Do not download or run the file, delete the message",
    "Run a full antivirus scan yourself right now",
    "Disconnect from network if files look encrypted",
    "Change passwords later from a clean device",
]


def _self_handled(steps: list, kind: str = "phishing") -> list:
    """Drop deflect-to-someone-else steps, refill with self-actions (3-5 kept)."""
    clean = [s for s in steps if not any(k in str(s).lower() for k in _DEFLECT_KEYS)]
    pool = _SELF_POOL
    if kind == "sqli":
        pool = _DEV_SQLI_POOL
    elif kind == "xss":
        pool = _DEV_XSS_POOL
    elif kind == "otp":
        pool = _OTP_POOL
    elif kind == "bec":
        pool = _BEC_POOL
    elif kind == "malware":
        pool = _MAL_POOL
    for cand in pool:
        if len(clean) >= 4:
            break
        if cand.lower() not in (str(s).lower() for s in clean):
            clean.append(cand)
    return clean[:5]


# ---------- §3 DIAGNOSE: auto-find problem -> LLM guide -> clean steps ----------
def diagnose(question: str, employee_id: str = "") -> dict:
    """Auto-find the problem: offline signals + LLM verdict + guided fix."""
    q = (question or "").strip()
    if not q:
        return {"verdict": "error", "kind": "safe", "reason": "Empty question. Type your problem first."}

    rules = screen(q)
    try:
        det = detect(q, "")
    except Exception as exc:  # detector never crashes, but stay safe
        det = {"verdict": "safe", "kind": "safe", "severity": "low", "reason": str(exc)[:80],
               "score": rules["score"], "signals": rules["signals"]}
    det_kind = str(det.get("kind", "phishing") or "phishing").lower()

    prompt = (
        f"QUESTION: {q}\n"
        f"SIGNALS: {json.dumps(rules)}\n"
        f"DETECTOR: {json.dumps({k: det.get(k) for k in ('kind', 'verdict', 'severity', 'reason')})}"
    )
    try:
        raw = generate(prompt, system=_PROMPT)
        start, end = raw.find("{"), raw.rfind("}")
        guide = json.loads(raw[start:end + 1]) if start >= 0 and end > start else {}
    except Exception as exc:
        return {
            "verdict": "error",
            "kind": det_kind,
            "severity": det.get("severity", "medium"),
            "reason": str(exc)[:150],
            "signals": rules["signals"],
            "score": rules["score"],
            "question": q,
        }

    steps = [str(s)[:140] for s in guide.get("steps", [])][:5]
    if not steps:
        steps = ["Describe what you see on screen, then follow the voice guide step by step."]
    steps = _self_handled(steps, kind=det_kind)
    severity = guide.get("severity", det.get("severity", "medium"))
    if rules["score"] >= 0.6 and severity in ("low", "medium"):
        severity = "high"
    if det_kind in ("sqli", "xss", "malware") and severity != "high":
        severity = "high"
    voice_script = str(guide.get("voice_script", " ".join(steps)))[:600]
    if any(k in voice_script.lower() for k in _DEFLECT_KEYS):
        voice_script = " ".join(steps)[:600]  # rebuild from clean steps
    return {
        "verdict": det.get("verdict", "safe"),
        "kind": det_kind,
        "problem": str(guide.get("problem", "Support request"))[:100],
        "severity": severity,
        "reason": det.get("reason", ""),
        "steps": steps,
        "voice_script": voice_script,
        "signals": rules["signals"],
        "score": rules["score"],
        "question": q,
        "employee_id": employee_id,
    }
