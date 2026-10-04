# CONTRIBUTION: Eval-Big — rules vs TF-IDF centroid ML on 2000 (no LLM, no cost).
"""External ML baseline in pure python (no pip). Proves pipeline scales beyond seed70.

RUN: .venv\\Scripts\\python -m tests.eval_big [--csv data/eval/labels2000.csv]
OUT: docs/EVAL_BIG.csv + docs/EVAL_BIG_summary.json + docs/EVAL_TABLES.md (Q1 tables)

Method: tokenize, TF-IDF on train-80%, centroid per kind, cosine nearest on test-20%.
Honest: simple ML, NOT XGBoost. XGBoost + public IEEE-CIS = next step (needs pip + gated data).
"""
import csv
import json
import math
import random
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from src.detection.rules import screen  # noqa: E402

TOK = re.compile(r"[a-z0-9]+(?:'[a-z]+)?")


def tok(s: str):
    return TOK.findall((s or "").lower())


def load(path: Path):
    rows = []
    with open(path, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            rows.append((r["title"], r.get("body", ""), r["label"].strip().lower()))
    return rows


def tfidf_vecs(docs):
    df = Counter()
    tfs = []
    for d in docs:
        c = Counter(tok(d))
        tfs.append(c)
        for t in c:
            df[t] += 1
    N = len(docs)
    idf = {t: math.log((1 + N) / (1 + n)) + 1 for t, n in df.items()}
    vecs = []
    for c in tfs:
        tot = sum(c.values()) or 1
        v = {t: (n / tot) * idf[t] for t, n in c.items()}
        nrm = math.sqrt(sum(x * x for x in v.values())) or 1
        vecs.append({t: x / nrm for t, x in v.items()})
    return vecs, idf


def centroid(vecs):
    c = defaultdict(float)
    for v in vecs:
        for t, x in v.items():
            c[t] += x
    n = len(vecs) or 1
    c = {t: x / n for t, x in c.items()}
    nrm = math.sqrt(sum(x * x for x in c.values())) or 1
    return {t: x / nrm for t, x in c.items()}


def cos(a, b):
    if len(a) > len(b):
        a, b = b, a
    return sum(x * b.get(t, 0.0) for t, x in a.items())


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", default="data/eval/labels2000_v2.csv")
    a = ap.parse_args()
    data = load(ROOT / a.csv)
    random.seed(7)
    by_kind = defaultdict(list)
    for r in data:
        by_kind[r[2]].append(r)
    train, test = [], []
    for k, rs in by_kind.items():
        random.shuffle(rs)
        cut = int(len(rs) * 0.8)
        train += rs[cut * 0 // 1:cut] if False else rs[:cut]
        test += rs[cut:]
    # TF-IDF ML
    tr_docs = [f"{t} {b}" for t, b, _ in train]
    vecs, idf = tfidf_vecs(tr_docs)
    cents = {}
    for k in by_kind:
        idx = [i for i, (_, _, kk) in enumerate(train) if kk == k]
        cents[k] = centroid([vecs[i] for i in idx])
    N = len(tr_docs)
    def vec_of(s):
        c = Counter(tok(s))
        tot = sum(c.values()) or 1
        v = {t: (n / tot) * (idf.get(t, math.log(N + 1)) + 0) for t, n in c.items()}
        nrm = math.sqrt(sum(x * x for x in v.values())) or 1
        return {t: x / nrm for t, x in v.items()}
    # score
    res = {"rules": [], "ml": []}
    for title, body, label in test:
        s = screen(f"{title}\n{body}")
        rp = "safe" if s["score"] < 0.30 else "attack"
        res["rules"].append((label, rp))
        v = vec_of(f"{title} {body}")
        best = max(cents, key=lambda k: cos(v, cents[k]))
        res["ml"].append((label, best))
    out_lines = [f"## Eval-Big (2000 synthetic-v1, test-20pct n={len(test)})", ""]
    summaries = {}
    for name in ("rules", "ml"):
        pairs = res[name]
        if name == "rules":
            tp = sum(1 for t, p in pairs if t != "safe" and p == "attack")
            tn = sum(1 for t, p in pairs if t == "safe" and p == "safe")
            fp = sum(1 for t, p in pairs if t == "safe" and p == "attack")
            fn = sum(1 for t, p in pairs if t != "safe" and p != "attack")
            acc = (tp + tn) / len(pairs)
            prec = tp / max(1, tp + fp)
            rec = tp / max(1, tp + fn)
            f1 = 2 * prec * rec / max(1e-9, prec + rec)
            summaries[name] = {"acc": round(acc, 3), "f1": round(f1, 3), "fp": fp, "fn": fn}
            out_lines += [f"- rules: acc={acc:.3f} F1={f1:.3f} FP={fp} FN={fn}", ""]
        else:
            ok = sum(1 for t, p in pairs if t == p)
            acc = ok / len(pairs)
            per = {k: f"{sum(1 for t, p in pairs if t == k and p == k)}/{sum(1 for t, _ in pairs if t == k)}"
                   for k in by_kind}
            summaries[name] = {"kind_acc": round(acc, 3), "per_kind": per}
            out_lines += [f"- ml-centroid kind_acc={acc:.3f} {per}", ""]
    docs = ROOT / "docs"
    (docs / "EVAL_BIG_summary.json").write_text(json.dumps(
        {"csv": a.csv, "n_test": len(test), **summaries,
         "note": "synthetic-v1 disclosed; rules binary; ml kind-exact centroid; LLM excluded (cost)"}, indent=2))
    prev = docs / "EVAL_TABLES.md"
    prev.write_text("# Q1 Eval Tables (auto)\n\n" + "\n".join(out_lines)
                    + "\nNext: replace synthetic-v1 with public IEEE-CIS/Fraud-R1 + XGBoost.\n")
    print("\n".join(out_lines))
    print("saved docs/EVAL_BIG_summary.json + docs/EVAL_TABLES.md")


if __name__ == "__main__":
    main()
