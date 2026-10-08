# REAL data sources (written by download_real.py)

- PART 1 Fraud-R1: cloned upstream (64 files). Data-like files: README.md, dataset/FP-base-full/FP-base-Chinese.json, dataset/FP-base-full/FP-base-English.json, dataset/FP-levelup-full/FP-levelup-Chinese.json, dataset/FP-levelup-full/FP-levelup-English.json, requirement.txt
- PART 2 SMS: mirror CSV saved (UCI zip unavailable).
- PART 3 Nazario: saved (7811841 bytes). Columns/rows inspected by build_real_labels.py PART 3.
- PART 4 Payloads: saved (164778 bytes). Fields inspected by build_real_labels.py PART 4.

Raw files are NEVER hand-edited. Mapping to our 7 labels lives in build_real_labels.py.
