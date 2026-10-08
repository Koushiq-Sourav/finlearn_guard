# CONTRIBUTION: Build HONEST eval set from REAL public data (Q1 fix).
#
# WHAT this file does (5 parts, one per source + merge):
#   PART 0 - Shared constants: our 7 labels, full names, severities.
#   PART 1 - Fraud-R1 EN  (upstream/dataset/.../FP-base-English.json, 1,071)
#            category -> our label: phishing -> phishing,
#            fraudulent-service / network-friendship -> phishing,
#            impersonation / fake-job-posting -> bec.
#            (Fraud-R1 has no OTP class; OTP comes from SMS in PART 2.)
#   PART 2 - UCI SMS Spam (sms_spam/spam.csv, 5,574):
#            ham -> safe; spam with OTP/prize/urgent words -> otp;
#            other spam -> phishing.
#   PART 3 - Nazario phishing mail (phishing_email/Nazario.csv, 1,565, all label=1):
#            rows mentioning exe/apk/ransom/bitcoin/decrypt -> malware (lure TEXT);
#            rest -> phishing. (Binaries are out of scope; lure text is the scope.)
#   PART 4 - Web payloads (payloads/WEB_APPLICATION_PAYLOADS.jsonl, line-scanned):
#            id sqli-* -> sqli; id xss-* -> xss. Line scan (not json.load)
#            because one entry (sqli-020) has corrupt bytes in example_query.
#   PART 5 - Merge: cap per class (--per-class, default 300), deterministic
#            shuffle (seed 42), write labels_real.csv in PROJECT columns:
#            id,title,body,label,label_full,severity.
#
# WHAT it does NOT do:
#   - No synthetic padding. If a class has fewer real rows than the cap
#     (sqli/xss have 100 each upstream), output keeps the real count and
#     REPORTS it. Reviewer sees exact N per class.
#   - Never touches data/eval/labels2000_v2.csv (synthetic stays for comparison).
#
# RUN:
#   .venv\Scripts\python data\real\build_real_labels.py [--per-class 300]
# OUT:
#   data/real/labels_real.csv
#
# HONEST LIMITS (also in README_REAL_DATA.md, cite in paper Sec 6):
#   - Fraud-R1 EN only (prototype is English-only; ZH half excluded).
#   - SMS ham = short informal safe; email safe comes only via ham here
#     (no Enron benign downloaded - Kaggle login required).
#   - malware = lure TEXT, not binaries.

from __future__ import annotations

import argparse
import csv
import json
import random
import re
from pathlib import Path

# -- Folder of THIS script (= data/real). Input + output both under here. --
HERE = Path(__file__).parent
OUT = HERE / "labels_real.csv"

# ======================================================================
# PART 0 - Shared constants (same 7 labels as data/eval/build_2000.py)
# ======================================================================
FULL = {
    "phishing": "Phishing (Generic Deception)",
    "otp": "OTP / Vishing Fraud",
    "bec": "Business Email Compromise",
    "sqli": "SQL Injection",
    "xss": "Cross-Site Scripting",
    "malware": "Malware / Ransomware",
    "safe": "Benign (Safe Communication)",
}
SEV = {"phishing": "high", "otp": "high", "bec": "high", "sqli": "high",
       "xss": "high", "malware": "high", "safe": "low"}

# Words that mark an SMS spam as OTP-style pressure (PART 2 rule).
OTP_WORDS = ("otp", "code", "verify", "verification", "prize", "won",
             "winner", "urgent", "call now", "call back", "free", "cash",
             "claim", "kidney", "account")
# Words that mark a phishing mail as a MALWARE lure (PART 3 rule).
MAL_WORDS = (".exe", ".apk", "ransom", "bitcoin", "decrypt", "install",
             "attachment", "invoice.doc")


# ======================================================================
# HELPERS - tiny text cleaners shared by all PARTs
# ======================================================================
def clean(text: str, limit: int = 800) -> str:
    """Collapse whitespace, strip, truncate to `limit` chars (one line)."""
    text = re.sub(r"\s+", " ", str(text or "")).strip()
    return text[:limit]


def title_of(text: str, nwords: int = 10) -> str:
    """First `nwords` words of `text` - used when a source has no title."""
    words = clean(text).split()
    return " ".join(words[:nwords]) or "(no title)"


# ======================================================================
# PART 1 - Fraud-R1 English base (1,071 real fraud dialogues)
# File: fraud_r1/upstream/dataset/FP-base-full/FP-base-English.json
# Row keys: id, category, subcategory, raw_data, data_type, language, ...
# ======================================================================
def part1_fraud_r1() -> list[dict]:
    path = (HERE / "fraud_r1" / "upstream" / "dataset"
            / "FP-base-full" / "FP-base-English.json")
    rows = json.loads(path.read_text(encoding="utf-8"))
    # Category -> our 7 labels (documented; Fraud-R1 has no OTP class).
    cat2label = {
        "phishing": "phishing",
        "fraudulent service": "phishing",
        "network friendship": "phishing",
        "impersonation": "bec",
        "fake job posting": "bec",
    }
    out = []
    for r in rows:
        label = cat2label.get(str(r.get("category", "")).lower())
        if label is None:  # unknown future category - skip loudly, never guess
            continue
        body = clean(r.get("raw_data", ""))
        if not body:
            continue
        out.append({
            "title": f"[{r.get('category')}] {r.get('subcategory', '')}"[:120],
            "body": body,
            "label": label,
            "src": "fraud-r1-en",
        })
    print(f"PART 1 Fraud-R1: {len(out)} rows "
          f"({sum(1 for x in out if x['label'] == 'phishing')} phishing, "
          f"{sum(1 for x in out if x['label'] == 'bec')} bec)")
    return out


# ======================================================================
# PART 2 - UCI SMS Spam (5,574 SMS; cols v1=ham/spam, v2=text)
# File: sms_spam/spam.csv (GitHub mirror of the UCI file; same content)
# ======================================================================
def part2_sms() -> list[dict]:
    path = HERE / "sms_spam" / "spam.csv"
    out = []
    with open(path, encoding="utf-8", errors="replace") as f:
        for row in csv.DictReader(f):
            label_raw = (row.get("v1", "") or "").strip().lower()
            text = clean(row.get("v2", ""))
            if not text:
                continue
            if label_raw == "ham":
                out.append({"title": title_of(text, 8), "body": text,
                            "label": "safe", "src": "sms-ham"})
            elif label_raw == "spam":
                low = text.lower()
                # OTP-style pressure? -> otp, else generic lure -> phishing.
                label = ("otp" if any(w.lower() in low for w in OTP_WORDS)
                         else "phishing")
                out.append({"title": title_of(text, 8), "body": text,
                            "label": label, "src": "sms-spam"})
    from collections import Counter
    print(f"PART 2 SMS: {len(out)} rows {dict(Counter(x['label'] for x in out))}")
    return out


# ======================================================================
# PART 3 - Nazario phishing mail (1,565 rows, label column always '1')
# Cols: sender,receiver,date,subject,body,urls,label
# NOTE: csv.field_size_limit is raised - mail bodies exceed the default.
# ======================================================================
def part3_nazario() -> list[dict]:
    import csv as _csv
    _csv.field_size_limit(10 * 1024 * 1024)
    path = HERE / "phishing_email" / "Nazario.csv"
    out = []
    with open(path, encoding="utf-8", errors="replace") as f:
        for row in _csv.DictReader(f):
            subject = clean(row.get("subject", ""), 200)
            body = clean(f"{subject} {row.get('body', '')}")
            if not body:
                continue
            low = body.lower()
            # Malware LURE text (exe/apk/ransom/...) -> malware, else phishing.
            label = ("malware" if any(w in low for w in MAL_WORDS)
                     else "phishing")
            out.append({"title": subject or title_of(body),
                        "body": body, "label": label, "src": "nazario"})
    from collections import Counter
    print(f"PART 3 Nazario: {len(out)} rows "
          f"{dict(Counter(x['label'] for x in out))}")
    return out


# ======================================================================
# PART 4 - Web payloads: sqli-* -> sqli, xss-* -> xss (LINE SCAN)
# Why line scan: the file is one JSON array but entry sqli-020 carries
# corrupt bytes in `example_query`, so json.load() dies at line 181.
# Each entry keeps id/payload/type on its OWN line, so we scan lines and
# only read the three fields we need. Corrupt lines are skipped, never
# crash the build.
# ======================================================================
def part4_payloads() -> list[dict]:
    path = HERE / "payloads" / "WEB_APPLICATION_PAYLOADS.jsonl"
    cur_id, cur_payload, cur_type = "", "", ""
    out, skipped = [], 0

    def flush() -> None:
        if cur_id.startswith("sqli-"):
            label = "sqli"
        elif cur_id.startswith("xss-"):
            label = "xss"
        else:
            return  # csrf/ssrf/cmdi - not our 7 labels, skip by design
        if not cur_payload:
            return
        out.append({
            "title": f"{cur_id}: {cur_type} payload",
            "body": (f"Attack input ({cur_type}): {cur_payload}. "
                     f"Submitted where user input is accepted."),
            "label": label, "src": "payloads",
        })

    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        s = line.strip()
        m = re.match(r'"id":\s*"([^"]+)"', s)
        if m:
            if cur_id:  # previous entry complete - store it first
                try:
                    flush()
                except Exception:  # noqa: BLE001 - one bad entry never kills build
                    skipped += 1
            cur_id, cur_payload, cur_type = m.group(1), "", ""
            continue
        m = re.match(r'"payload":\s*"(.*)"\s*,?\s*$', s)
        if m and cur_id:
            cur_payload = m.group(1)
            continue
        m = re.match(r'"type":\s*"([^"]+)"', s)
        if m and cur_id:
            cur_type = m.group(1)
    if cur_id:
        try:
            flush()
        except Exception:  # noqa: BLE001
            skipped += 1
    from collections import Counter
    print(f"PART 4 Payloads: {len(out)} rows "
          f"{dict(Counter(x['label'] for x in out))} (skipped {skipped})")
    return out


# ======================================================================
# PART 5 - Merge with per-class caps + deterministic shuffle + write CSV
# Same columns as data/eval/labels2000_v2.csv (paper tables stay valid).
# ======================================================================
def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--per-class", type=int, default=300,
                    help="max rows kept per label (default 300)")
    a = ap.parse_args()

    pool: dict[str, list[dict]] = {k: [] for k in FULL}
    for row in part1_fraud_r1() + part2_sms() + part3_nazario() + part4_payloads():
        pool[row["label"]].append(row)

    # Cap each class IN SOURCE ORDER then shuffle deterministically (seed 42)
    # so rebuilds are byte-identical - reviewer can reproduce exactly.
    kept: list[dict] = []
    for label, rows in pool.items():
        take = rows[:a.per_class]
        kept.extend(take)
        print(f"  {label:8s}: available {len(rows):5d} -> kept {len(take)}")
    random.seed(42)
    random.shuffle(kept)

    with open(OUT, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["id", "title", "body",
                                          "label", "label_full", "severity"])
        w.writeheader()
        for i, r in enumerate(kept, 1):
            w.writerow({"id": f"FLG-R{i:05d}", "title": r["title"],
                        "body": r["body"], "label": r["label"],
                        "label_full": FULL[r["label"]],
                        "severity": SEV[r["label"]]})
    print(f"WROTE {OUT} ({len(kept)} REAL rows, 0 synthetic)")


if __name__ == "__main__":
    main()
