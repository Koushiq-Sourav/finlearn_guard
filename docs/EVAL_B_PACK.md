# Eval B — Learning Proof Pack (needs 30 humans, you run it)

Goal for Q1: prove Support teaches. Two groups, 15 min, pre/post quiz.

## Protocol (45 min total per batch)
1. Consent 1 page (voluntary, anonymized, data stays on your PC).
2. Pre-quiz 10 Qs (5 min): 2 phishing spot, 2 OTP, 2 BEC, 2 sqli/xss recognize, 2 safe-vs-scam.
3. Group A (control): read static PDF tips 15 min. Group B: use /support ask 3 Qs + play voice + video 15 min.
4. Post-quiz same 10 Qs shuffled (5 min) + SUS 5 Qs (usability).
5. Score: need Group B uplift >= +15% and p<0.05 (paired t-test).

## Quiz (use as-is, answers sealed)
1. OTP on WhatsApp from unknown — safe? (No)
2. CEO mail wire urgently — first step? (verify second channel)
3. Invoice bank changed — wire? (No, call vendor)
4. `admin'--` in login — attack? (sqli)
5. `<img onerror=...>` — attack? (xss)
6. statement.exe invoice — run? (No, malware)
7. QR to verify login — scan? (No, open official app)
8. Gift cards for client — buy? (No, BEC)
9. Team lunch mail — safe? (Yes)
10. Prize + OTP — share? (No)

## Files to fill (keep in docs/, never push names)
- docs/EVAL_B_scores.csv: id,group,pre,post (numbers only)
- Run t-test in Excel/Sheets: =TTEST(postB,preB,2,1), same for A.

## Honest note for paper
Report N, mean uplift A vs B, p-value, limits (students only, single session).
No humans = no Q1 learning claim. System + detection alone = Q3 max.
