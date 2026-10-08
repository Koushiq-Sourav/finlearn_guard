# CONTRIBUTION: Real figures for Q1 Sec 6 (plotted from EVAL_R_summary.json).
#
# WHAT: reads docs/EVAL_R_summary.json, writes 2 PNGs to docs/figs/:
#   FIG 1 fig_evalR_F1.png - binary F1 bars: rules (1,494) vs XGB (test 299)
#                              vs hybrid sample (70). Same metric, honest N labels.
#   FIG 2 fig_perkind_recall.png - per-kind recall bars: rules vs XGB.
#                              Shows the honest weakness (rules miss real
#                              phishing/otp/bec phrasing) and the fix (XGB/hybrid).
# RUN: .venv\Scripts\python docs\figs\make_figs.py
# NOTE for Overleaf: upload the whole docs/figs/ folder next to the .tex.
"""Plot Eval-R figures from measured JSON (no hand-typed numbers)."""
import json
from pathlib import Path

HERE = Path(__file__).parent
SUMMARY = HERE.parent / "EVAL_R_summary.json"


def main() -> None:
    import matplotlib
    matplotlib.use("Agg")  # headless: no window ever pops up
    import matplotlib.pyplot as plt

    s = json.loads(SUMMARY.read_text(encoding="utf-8"))
    kinds = ["phishing", "otp", "bec", "sqli", "xss", "malware", "safe"]

    # FIG 1 - binary F1 on real data (N shown: different honest denominators).
    fig, ax = plt.subplots(figsize=(7.5, 3.6))
    f1s = [s["rules_all"]["F1"], s["xgb_80_20"]["F1"],
           s["hybrid_sample"]["F1"]]
    labels = ["rules\n(n=1494)", "TF-IDF+XGB\n(test n=299)",
              "hybrid sample\n(n=70)"]
    bars = ax.bar(labels, f1s)
    ax.set_ylim(0, 1.05)
    ax.set_ylabel("binary F1 (attack vs safe)")
    ax.set_title("Eval-R: binary F1 on REAL rows (higher is better)")
    for b, v in zip(bars, f1s):
        ax.text(b.get_x() + b.get_width() / 2, v + 0.02, f"{v:.3f}",
                ha="center", fontsize=10)
    fig.tight_layout()
    fig.savefig(HERE / "fig-evalR-F1.png", dpi=150)
    print("wrote fig-evalR-F1.png", f1s)

    # FIG 2 - per-kind recall: rules (all 1,494) vs XGB (test 299).
    fig, ax = plt.subplots(figsize=(8.5, 3.8))
    r = [s["rules_all"]["per_kind_recall"][k] for k in kinds]
    x = [s["xgb_80_20"]["per_kind_recall"][k] for k in kinds]
    pos = range(len(kinds))
    w = 0.38
    ax.bar([p - w / 2 for p in pos], r, width=w, label="rules (n=1494)")
    ax.bar([p + w / 2 for p in pos], x, width=w, label="XGB (test n=299)")
    ax.set_xticks(list(pos))
    ax.set_xticklabels(kinds, rotation=20)
    ax.set_ylim(0, 1.05)
    ax.set_ylabel("recall per kind")
    ax.set_title("Eval-R: per-kind recall, rules vs TF-IDF+XGB (honest gap)")
    ax.legend()
    fig.tight_layout()
    fig.savefig(HERE / "fig-perkind-recall.png", dpi=150)
    print("wrote fig-perkind-recall.png")


if __name__ == "__main__":
    main()
