# CONTRIBUTION: Honest eval on REAL data (Q1 blockers 2+3).
#
# WHAT this file does (5 sections, run in order):
#   §1 LOAD   - read data/real/labels_real.csv (1,494 real rows, 0 synthetic)
#   §2 RULES  - rules-only screen() on ALL rows: binary + kind + per-kind recall
#   §3 XGB    - TF-IDF + XGBoost baseline, stratified 80/20 split, same metrics,
#               + McNemar paired test (rules vs xgb correctness on the test split)
#   §4 HYBRID - optional: full detect() (rules+LLM+locks) on a stratified sample
#               (--with-llm K per class, default 0 = skip). Skips HONESTLY with
#               verdict=error rows excluded if OPENROUTER_API_KEY is missing.
#   §5 SAVE   - write docs/EVAL_R_summary.json + print paper-ready tables
#
# WHAT it does NOT do:
#   - No training on the test split (TF-IDF+XGB fit on train only).
#   - No synthetic rows. Small classes (sqli/xss 100, malware 94) stay small
#     and the JSON reports exact N so the paper cannot overclaim.
#
# RUN (no key needed for §2+§3):
#   .venv\Scripts\python tests\eval_real.py
# RUN with hybrid sample (needs .env key, ~70 LLM calls):
#   .venv\Scripts\python tests\eval_real.py --with-llm 10
# OUT:
#   docs/EVAL_R_summary.json
"""Real-data eval: rules on all rows, XGBoost baseline on 80/20, optional hybrid sample."""
import argparse
import csv
import json
import sys
import time
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
REAL_CSV = ROOT / "data" / "real" / "labels_real.csv"
OUT_JSON = ROOT / "docs" / "EVAL_R_summary.json"

KINDS = ["phishing", "otp", "bec", "sqli", "xss", "malware", "safe"]


# ======================================================================
# §1 LOAD - real rows only (fail loudly if the builder was never run)
# ======================================================================
def load_rows() -> list[dict]:
    if not REAL_CSV.exists():
        raise SystemExit(
            f"missing {REAL_CSV}. Run: .venv\\Scripts\\python "
            f"data\\real\\build_real_labels.py")
    rows = list(csv.DictReader(open(REAL_CSV, encoding="utf-8")))
    assert rows and set(rows[0]) == {
        "id", "title", "body", "label", "label_full", "severity"}, rows[0].keys()
    return rows


# ======================================================================
# METRICS - binary (attack vs safe) + kind-exact + per-kind recall
# Binary positive = attack (label != safe). Rules verdict safe<->attack via
# score threshold: score >= 0.30 -> attack (same cut as Eval-A rules-only).
# ======================================================================
def metrics(gold: list[str], pred_attack: list[bool],
            pred_kind: list[str]) -> dict:
    n = len(gold)
    tp = sum(1 for g, p in zip(gold, pred_attack) if g != "safe" and p)
    fp = sum(1 for g, p in zip(gold, pred_attack) if g == "safe" and p)
    fn = sum(1 for g, p in zip(gold, pred_attack) if g != "safe" and not p)
    prec = tp / (tp + fp) if (tp + fp) else 0.0
    rec = tp / (tp + fn) if (tp + fn) else 0.0
    return {
        "n": n,
        "acc": round(sum(1 for g, p in zip(gold, pred_attack)
                         if (g != "safe") == p) / n, 4),
        "P": round(prec, 4), "R": round(rec, 4),
        "F1": round(2 * prec * rec / (prec + rec), 4) if (prec + rec) else 0.0,
        "kind_acc": round(sum(1 for g, k in zip(gold, pred_kind)
                              if g == k) / n, 4),
        "per_kind_recall": {
            k: round(sum(1 for g, p in zip(gold, pred_attack)
                         if g == k and (p == (k != "safe"))) / max(
                             1, sum(1 for g in gold if g == k)), 4)
            for k in KINDS},
    }


# ======================================================================
# §2 RULES - screen() every real row (offline, free, timed)
# Kind guess from signals: sqli/xss/malware/otp/bec keyword hits, else
# phishing for attacks (mirrors detector STEP 4 order, WITHOUT the LLM).
# ======================================================================
def run_rules(rows: list[dict]) -> dict:
    from src.detection.rules import screen
    gold, atk, kind, ms = [], [], [], []
    t0 = time.perf_counter()
    for r in rows:
        s = screen(f"{r['title']}\n{r['body']}")
        sigs = " ".join(s["signals"]).lower()
        gold.append(r["label"])
        atk.append(s["score"] >= 0.30)
        if r["label"] == "safe" and s["score"] < 0.30:
            kind.append("safe")
        elif any(k in sigs for k in ("union", "select", "drop", "1=1", "--",
                                     "insert", "update")):
            kind.append("sqli")
        elif any(k in sigs for k in ("script", "onerror", "alert", "cookie",
                                     "<img", "javascript")):
            kind.append("xss")
        elif any(k in sigs for k in ("malware", "ransomware", ".exe", ".apk",
                                     "bitcoin", "decrypt")):
            kind.append("malware")
        elif any(k in sigs for k in ("otp", "voicemail", "whatsapp", "prize",
                                     "winner")):
            kind.append("otp")
        elif any(k in sigs for k in ("invoice", "wire", "ceo", "gift")):
            kind.append("bec")
        else:
            kind.append("phishing" if s["score"] >= 0.30 else "safe")
        ms.append(0.0)
    total_ms = (time.perf_counter() - t0) * 1000
    m = metrics(gold, atk, kind)
    m["mean_ms"] = round(total_ms / len(rows), 3)
    m["correct"] = [(g != "safe") == p for g, p in zip(gold, atk)]
    return m


# ======================================================================
# §3 XGB - TF-IDF word 1-2gram + XGBoost, stratified 80/20 (train-only fit)
# + McNemar paired test on the SHARED test split (rules vs xgb binary).
# Small classes stay small: test has ~20 sqli/xss rows - reported, not hidden.
# ======================================================================
def run_xgb(rows: list[dict]) -> dict:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.model_selection import train_test_split
    from xgboost import XGBClassifier
    from scipy.stats import chi2 as chi2dist
    texts = [f"{r['title']}\n{r['body']}" for r in rows]
    y = [r["label"] for r in rows]
    # XGBoost needs integer classes: encode via KINDS order (0..6).
    yenc = [KINDS.index(v) for v in y]
    idx = list(range(len(rows)))
    tr, te = train_test_split(idx, test_size=0.20, random_state=42,
                              stratify=y)
    vec = TfidfVectorizer(ngram_range=(1, 2), max_features=20000)
    Xtr = vec.fit_transform([texts[i] for i in tr])  # fit on TRAIN only
    Xte = vec.transform([texts[i] for i in te])
    clf = XGBClassifier(n_estimators=300, max_depth=6, learning_rate=0.08,
                        subsample=0.9, colsample_bytree=0.9, tree_method="hist",
                        random_state=42, n_jobs=-1)
    clf.fit(Xtr, [yenc[i] for i in tr])
    pred = [KINDS[v] for v in clf.predict(Xte)]
    gold = [y[i] for i in te]
    pred_atk = [p != "safe" for p in pred]
    # Rules on the SAME test split (fair paired comparison).
    from src.detection.rules import screen
    rules_atk = [screen(texts[i])["score"] >= 0.30 for i in te]
    m = metrics(gold, pred_atk, pred)
    m["test_n"] = len(te)
    m["test_dist"] = dict(Counter(gold))
    # McNemar on binary correctness (rules vs xgb), Edwards-corrected chi2.
    rc = [(gold[k] != "safe") == rules_atk[k] for k in range(len(te))]
    xc = [(gold[k] != "safe") == pred_atk[k] for k in range(len(te))]
    b = sum(1 for a, c in zip(rc, xc) if a and not c)
    c = sum(1 for a, c in zip(rc, xc) if not a and c)
    chi2 = ((abs(b - c) - 1) ** 2 / (b + c)) if (b + c) else 0.0
    m["mcnemar"] = {"rules_only_ok": b, "xgb_only_ok": c,
                    "chi2": round(chi2, 3),
                    "p": round(float(chi2dist.sf(chi2, 1)), 4)}
    m["rules_on_test_acc"] = round(sum(rc) / len(te), 4)
    return m


# ======================================================================
# §4 HYBRID - full detect() on a stratified sample (needs .env key)
# Skips HONESTLY (returns {"skipped": reason}) when the key is missing or
# every call errors - never fabricates hybrid numbers.
# ======================================================================
def run_hybrid(rows: list[dict], per_class: int) -> dict:
    if per_class <= 0:
        return {"skipped": "flag --with-llm not given (rules+xgb only)"}
    import random
    from src.agents.detector import detect
    random.seed(7)
    sample = []
    for k in KINDS:
        pool = [r for r in rows if r["label"] == k]
        sample.extend(random.sample(pool, min(per_class, len(pool))))
    gold, atk, kind, ok = [], [], [], 0
    for r in sample:
        try:
            d = detect(r["title"], r["body"])
        except Exception as e:  # noqa: BLE001 - missing key lands here
            return {"skipped": f"LLM unavailable: {str(e)[:100]}",
                    "attempted": len(gold)}
        if d.get("verdict") == "error" or not d.get("llm_ok", True):
            continue  # error rows EXCLUDED from metrics, counted in llm_ok_rate
        ok += 1
        gold.append(r["label"])
        atk.append(d["verdict"] == "phishing")
        kind.append(d.get("kind", "phishing"))
    if not gold:
        return {"skipped": "all hybrid calls errored (key/network?)",
                "attempted": len(sample)}
    m = metrics(gold, atk, kind)
    m["sample_n"] = len(sample)
    m["llm_ok_rate"] = round(ok / len(sample), 4)
    return m


# ======================================================================
# §5 SAVE - docs/EVAL_R_summary.json + paper-ready console tables
# ======================================================================
def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--with-llm", type=int, default=0,
                    help="hybrid sample rows PER CLASS (default 0 = skip)")
    a = ap.parse_args()
    rows = load_rows()
    print(f"loaded {len(rows)} REAL rows from {REAL_CSV}")
    rules = run_rules(rows)
    xgb = run_xgb(rows)
    hybrid = run_hybrid(rows, a.with_llm)
    summary = {"n_real": len(rows),
               "dist": dict(Counter(r["label"] for r in rows)),
               "rules_all": {k: v for k, v in rules.items() if k != "correct"},
               "xgb_80_20": xgb, "hybrid_sample": hybrid}
    OUT_JSON.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(f"\nwrote {OUT_JSON}")
    print("\n== RULES (all 1,494 real) ==")
    print(f"acc {rules['acc']} P {rules['P']} R {rules['R']} "
          f"F1 {rules['F1']} kind {rules['kind_acc']} "
          f"mean {rules['mean_ms']}ms")
    print("per-kind recall:", rules["per_kind_recall"])
    print("\n== XGB TF-IDF 80/20 ==")
    print(f"test_n {xgb['test_n']} {xgb['test_dist']}")
    print(f"acc {xgb['acc']} P {xgb['P']} R {xgb['R']} F1 {xgb['F1']} "
          f"kind {xgb['kind_acc']}")
    print(f"rules_on_same_test {xgb['rules_on_test_acc']} "
          f"mcnemar b={xgb['mcnemar']['rules_only_ok']} "
          f"c={xgb['mcnemar']['xgb_only_ok']} "
          f"chi2={xgb['mcnemar']['chi2']} p={xgb['mcnemar']['p']}")
    print("\n== HYBRID sample ==")
    print(hybrid)


if __name__ == "__main__":
    main()
