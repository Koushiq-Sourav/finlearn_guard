# CONTRIBUTION: One job only - DOWNLOAD the 4 real datasets (no login needed).
#
# WHAT this file does (4 parts, one per dataset):
#   PART 1 - Fraud-R1 : git clone --depth 1 the public benchmark repo into data/real/fraud_r1/
#   PART 2 - SMS Spam: download the UCI SMS Spam zip/txt into data/real/sms_spam/
#   PART 3 - Nazario : download the phishing-email CSV mirror into data/real/phishing_email/
#   PART 4 - Payloads: download the SQLi/XSS JSONL into data/real/payloads/
#
# WHAT it does NOT do:
#   - No label mapping here (that is build_real_labels.py).
#   - No model training, no eval. Download only.
#
# RUN:
#   .venv\Scripts\python data\real\download_real.py
# OUT:
#   data/real/fraud_r1/..., sms_spam/..., phishing_email/Nazario.csv,
#   payloads/WEB_APPLICATION_PAYLOADS.jsonl, plus SOURCES.md log.
#
# If a download fails (no internet / URL moved), the script STOPS with a
# clear message naming the PART - it never writes half files.

from __future__ import annotations

import subprocess
import urllib.request
import zipfile
from pathlib import Path

# -- Folder of THIS script (= data/real). All outputs stay under here. --
HERE = Path(__file__).parent


# ======================================================================
# HELPER - download one URL to one file (with progress + no half files)
# ======================================================================
def fetch(url: str, out: Path) -> None:
    """Download `url` to `out`. Writes to .part first, renames only on success."""
    out.parent.mkdir(parents=True, exist_ok=True)
    tmp = out.with_suffix(out.suffix + ".part")
    print(f"GET {url}")
    print(f" -> {out}")
    urllib.request.urlretrieve(url, tmp)  # raises on network/HTTP error
    tmp.replace(out)  # atomic: old file stays intact if download failed
    print(f"    saved {out.stat().st_size} bytes")


# ======================================================================
# PART 1 - Fraud-R1 benchmark repo (public GitHub, MIT)
# URL: https://github.com/kaustpradalab/Fraud-R1
# ======================================================================
def part1_fraud_r1() -> str:
    dest = HERE / "fraud_r1" / "upstream"
    if (dest / ".git").exists():
        print("PART 1 Fraud-R1: already cloned, pulling latest...")
        subprocess.run(["git", "-C", str(dest), "pull", "--ff-only"],
                       check=False)
    else:
        print("PART 1 Fraud-R1: cloning (depth 1, no history)...")
        dest.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(
            ["git", "clone", "--depth", "1",
             "https://github.com/kaustpradalab/Fraud-R1",
             str(dest)],
            check=True,
        )
    # Log what actually landed (reviewer can verify the source).
    files = sorted(p.relative_to(dest).as_posix()
                   for p in dest.rglob("*") if p.is_file())
    data_files = [f for f in files
                  if f.endswith((".json", ".jsonl", ".csv", ".txt", ".md"))]
    return (f"PART 1 Fraud-R1: cloned upstream ({len(files)} files). "
            f"Data-like files: {', '.join(data_files[:20])}")


# ======================================================================
# PART 2 - UCI SMS Spam Collection (public, CC BY 4.0, 5,574 SMS)
# Page: https://archive.ics.uci.edu/dataset/228/sms+spam+collection
# We try the static zip first, then fall back to known mirrors.
# ======================================================================
SMS_URLS = [
    # Primary: UCI static archive (same id=228 as the dataset page).
    "https://archive.ics.uci.edu/static/public/228/sms+spam+collection.zip",
    # Fallback: widely used GitHub mirror of the same UCI file.
    "https://raw.githubusercontent.com/mohitgupta-1O1/Kaggle-SMS-Spam-Collection-Dataset-/master/spam.csv",
]


def part2_sms() -> str:
    dest_dir = HERE / "sms_spam"
    dest_dir.mkdir(parents=True, exist_ok=True)
    last_err = ""
    for url in SMS_URLS:
        try:
            if url.endswith(".zip"):
                zpath = dest_dir / "sms_spam_collection.zip"
                fetch(url, zpath)
                with zipfile.ZipFile(zpath) as z:
                    z.extractall(dest_dir)
                return (f"PART 2 SMS: UCI zip saved "
                        f"({zpath.stat().st_size} bytes), extracted "
                        f"{len(list(dest_dir.iterdir()))} files.")
            else:
                fetch(url, dest_dir / "spam.csv")
                return "PART 2 SMS: mirror CSV saved (UCI zip unavailable)."
        except Exception as e:  # noqa: BLE001 - try next mirror, report last error
            last_err = f"{type(e).__name__}: {e}"
            print(f"    mirror failed: {last_err}")
    raise RuntimeError(f"PART 2 SMS: all mirrors failed. Last error: {last_err}")


# ======================================================================
# PART 3 - Nazario phishing emails (public GitHub mirror, ~7.5 MB CSV)
# URL: https://github.com/rokibulroni/Phishing-Email-Dataset (Nazario.csv)
# ======================================================================
def part3_nazario() -> str:
    out = HERE / "phishing_email" / "Nazario.csv"
    fetch("https://raw.githubusercontent.com/rokibulroni/Phishing-Email-Dataset/main/Nazario.csv",
          out)
    return (f"PART 3 Nazario: saved ({out.stat().st_size} bytes). "
            f"Columns/rows inspected by build_real_labels.py PART 3.")


# ======================================================================
# PART 4 - Web attack payloads: 100 SQLi + 100 XSS (+more), JSONL
# URL: https://github.com/SunnyThakur25/Web-Application-Payloads-Dataset
# ======================================================================
def part4_payloads() -> str:
    out = HERE / "payloads" / "WEB_APPLICATION_PAYLOADS.jsonl"
    fetch("https://raw.githubusercontent.com/SunnyThakur25/Web-Application-Payloads-Dataset/main/WEB_APPLICATION_PAYLOADS.jsonl",
          out)
    return (f"PART 4 Payloads: saved ({out.stat().st_size} bytes). "
            f"Fields inspected by build_real_labels.py PART 4.")


# ======================================================================
# MAIN - run PARTs 1-4 in order, then write SOURCES.md log
# ======================================================================
def main() -> None:
    notes = []
    notes.append(part1_fraud_r1())
    notes.append(part2_sms())
    notes.append(part3_nazario())
    notes.append(part4_payloads())
    log = HERE / "SOURCES.md"
    log.write_text(
        "# REAL data sources (written by download_real.py)\n\n"
        + "\n".join(f"- {n}" for n in notes)
        + "\n\nRaw files are NEVER hand-edited. "
          "Mapping to our 7 labels lives in build_real_labels.py.\n",
        encoding="utf-8",
    )
    print("\nDONE. " + "\n".join(notes))
    print(f"Wrote {log}")


if __name__ == "__main__":
    main()
