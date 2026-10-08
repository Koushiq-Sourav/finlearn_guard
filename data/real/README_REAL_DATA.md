# REAL data for FinLearn Guard (Q1 fix: replace synthetic Eval-Big)

> **CONTRIBUTION:** This folder holds REAL public datasets only.
> Synthetic `data/eval/labels2000_v2.csv` stays untouched for comparison.
> New honest eval file built here: `data/real/labels_real.csv`
> (same columns: `id,title,body,label,label_full,severity`).

## Which dataset feeds which of our 7 labels

| Folder | Source (public, no login) | Exact URL | Size | License | Our labels |
|---|---|---|---|---|---|
| `fraud_r1/` | Fraud-R1 benchmark (ACL Findings 2025), 8,564 fraud/phishing, EN+ZH | `https://github.com/kaustpradalab/Fraud-R1` | ~8.5k cases | MIT (repo) | phishing, bec (impersonation / fake-job / services) |
| `sms_spam/` | UCI SMS Spam Collection, 5,574 SMS ham/spam | `https://archive.ics.uci.edu/dataset/228/sms+spam+collection` | 466 KB | CC BY 4.0 | otp (spam w/ OTP/prize/urgent), safe (ham), phishing (other spam) |
| `phishing_email/` | Nazario phishing corpus mirror (subset of the 82k Kaggle mix) | `https://github.com/rokibulroni/Phishing-Email-Dataset/blob/main/Nazario.csv` | ~7.5 MB | research use | phishing (malware-lure subset -> malware) |
| `payloads/` | Web-Application-Payloads (100 SQLi + 100 XSS + more, JSONL) | `https://github.com/SunnyThakur25/Web-Application-Payloads-Dataset` | 300 rows | free use | sqli, xss |

## Scripts (each file = one job, read top comment first)

| File | Job |
|---|---|
| `download_real.py` | PART 1-4: downloads the 4 sources above into their folders. Run once. |
| `build_real_labels.py` | PART 1-5: converts raw files -> `labels_real.csv` in project columns. Heavily commented per source. |
| `labels_real.csv` | OUTPUT: real eval set (built, not hand-edited). |
| `SOURCES.md` | Per-file log: exact file downloaded, rows, date, URL. Written by `download_real.py`. |

## How to reproduce (2 commands)

```bat
.venv\Scripts\python data\real\download_real.py
.venv\Scripts\python data\real\build_real_labels.py --per-class 300
```

## Notes for the reviewer (honest limits)

- Fraud-R1 is bilingual EN+ZH; we keep EN only for this English-only prototype and note it.
- SMS ham = short informal text; email safe = longer formal text. Both map to `safe` but style differs - noted in `labels_real.csv` source column? No: output keeps exact project columns only (no extra column), source mix is logged here and in builder comments.
- `malware` here = lure TEXT about exe/apk/ransom (not binaries). Binaries are out of scope by design.
- IEEE-CIS tabular (1.35 GB, Kaggle login) intentionally NOT downloaded: wrong shape for a text detector; used only as cited baseline method, not input.
