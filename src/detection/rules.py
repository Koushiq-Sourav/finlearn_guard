# CONTRIBUTION: Offline danger-word scorer that works without any AI key.
"""Fast offline rules screener. Returns score 0..1 + matched signals.

SECTIONS:
  §1 PATTERNS - 14 rows: phishing + bec/otp pools + malware/QR + sqli + xss
  §2 SCORER   - match branches, sum weights, cap 1.0
"""
import re

# ---------- §1 PATTERN TABLE: danger regex -> weight ----------
# Edit this table to change what counts as dangerous (guide E8). Higher weight = more dangerous.
# Rows 1-8: phishing lures. Row 9-10: BEC/invoice-ceo. Row 11: OTP/vishing call.
# Row 12-13: malware/ransomware + QR/APK short-link. Row 14-15: SQLi/XSS.
# 7-kind taxonomy: phishing | otp | bec | sqli | xss | malware | safe
PATTERNS = [
    (r"verify.*account|account.*suspend|account.*locked", 0.35),
    (r"password|otp|one[- ]time|pin\b", 0.30),
    (r"urgent|immediately|within \d+ hours?|act now", 0.20),
    (r"http[s]?://|www\.|click.*link|login.*here", 0.20),
    (r"invoice|payment|wire|transfer|refund", 0.15),
    (r"prize|lottery|winner|congratulations.*won", 0.30),
    (r"\bceo\b|\bmanagement\b.*request|confidential.*transfer", 0.25),
    (r"free.*gift|claim.*now|limited.*offer", 0.15),
    (r"gift.*card|itunes.*card|google.*play.*card|buy.*card.*send.*code", 0.30),
    (r"call.*back|missed.*call|voicemail|whatsapp.*otp|vishing|call.*verify", 0.25),
    (r"malware|ransomware|trojan|spyware|\.exe\b|\.apk\b|decrypt.*pay|pay.*bitcoin|files.*encrypted", 0.40),
    (r"qr.*scan|scan.*qr|bit\.ly|tinyurl|t\.co/|short.*link|apk.*install", 0.20),
    (r"'.*or.*=|union.*select|drop.*table|insert.*into|select.*from|update.*set|delete.*from|--|xp_|1=1", 0.40),
    (r"<script|javascript:|onerror=|onload=|<img|alert\(|document\.cookie", 0.40),
]


# ---------- §2 SCORER: match every pattern, add weights, cap at 1.0 ----------
def screen(text: str) -> dict:
    """SCORER: match every pattern, add weights, cap at 1.0."""
    t = (text or "").lower()
    signals = []
    score = 0.0
    for pat, w in PATTERNS:
        m = re.search(pat, t)
        if m:
            # show the branch that actually matched, not just the first one
            hit = m.group(0)[:28]
            for branch in pat.split("|"):
                b = re.search(branch, t)
                if b:
                    hit = b.group(0)[:28]
                    break
            signals.append(hit)
            score += w
    return {"score": round(min(1.0, score), 2), "signals": signals}
