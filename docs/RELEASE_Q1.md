# Q1 Release Checklist (do before submit)

- [ ] `EVAL_A` 70 kind-exact rerun clean (docs/EVAL_A_summary.json)
- [ ] `EVAL_BIG` professional-v2 disclosed, real CSV path ready (data/eval/labels2000_v2.csv: id,title,body,label,label_full,severity)
- [ ] Eval B human scores in docs/EVAL_B_scores.csv (N>=30, anonymized, never push names)
- [ ] THESIS Ch5 rewritten with 3 tables: binary, per-kind, latency + confusion note (phishing/otp/bec overlap)
- [ ] Limits honest: synthetic-v1 overfits (ML 1.0), seed70 small, LLM needs key+net, video slides not avatar, no packet sniff
- [ ] GitHub public: code + 1000 anonymized events + requirements + reproduce.sh (pytest + eval_big, no key needed for rules/ML)
- [ ] `.env` NEVER pushed (gitignore ok). Rotate OpenRouter key + Mongo password after any leak.
- [ ] Targets: Expert Systems with Applications / Computers & Security / Computers & Education: AI (applied). Not theory journals.

Reproduce (no key):
  .venv\Scripts\python -m pytest tests -q
  .venv\Scripts\python -m tests.eval_big
With key (70 LLM):
  .venv\Scripts\python -m tests.eval_detection
