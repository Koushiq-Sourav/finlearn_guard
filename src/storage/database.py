# CONTRIBUTION: MongoDB reads/writes for employees, threats, and devices.
"""Storage layer: MongoDB only (Atlas).

SECTIONS:
  §1 SEED    - demo employees (Koushiq/Tumpa/Rahim)
  §2 CONNECT - client cache + ping, time helper, online rule
  §3 EMPLOYEES - list + add (auto ID E004+)
  §4 THREATS   - save + list + per-minute stats + perf summary
  §5 DEVICES   - register + heartbeat + list (online = seen < 120s)

Env:
  MONGO_URL=mongodb://127.0.0.1:27017 (default)
  MONGO_DB=finlearn_guard (default)

Public API:
  connect, init_db, list_employees, add_employee, save_threat,
  list_threats, threat_stats, perf_summary, set_risk,
  register_device, device_heartbeat, list_devices
"""
import os
from datetime import datetime, timezone

from dotenv import load_dotenv

load_dotenv()

# ---------- §1 SEED: 3 demo employees, inserted only when the collection is empty ----------
SEED_EMPLOYEES = [
    ("E001", "Koushiq", "Finance", "low"),
    ("E002", "Tumpa", "HR", "medium"),
    ("E003", "Rahim", "IT", "low"),
]


def _now_str() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")


# ---------- §2 CONNECT: client cache, clock, online rule ----------
_mongo_client = None


def _mongo_db():
    global _mongo_client
    from pymongo import MongoClient

    url = os.getenv("MONGO_URL", "mongodb://127.0.0.1:27017").strip()
    name = os.getenv("MONGO_DB", "finlearn_guard").strip() or "finlearn_guard"
    if _mongo_client is None:
        _mongo_client = MongoClient(url, serverSelectionTimeoutMS=3000)
        _mongo_client.admin.command("ping")
    return _mongo_client[name]


def _emp_doc(d: dict) -> dict:
    return {"id": d.get("_id"), "name": d.get("name", ""), "dept": d.get("dept", ""), "risk": d.get("risk", "low")}


def _threat_doc(d: dict) -> dict:
    return {
        "id": str(d.get("_id")),
        "title": d.get("title", ""),
        "kind": d.get("kind", "phishing"),
        "severity": d.get("severity", "medium"),
        "created_at": d.get("created_at", ""),
    }


ONLINE_SECONDS = 120  # heartbeat freshness window (devices page green/grey)


def _device_status(last_seen: str) -> str:
    """Online = heartbeat seen in last ONLINE_SECONDS (120s)."""
    try:
        dt = datetime.strptime(str(last_seen)[:19], "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
        age = (datetime.now(timezone.utc) - dt).total_seconds()
        return "online" if age <= ONLINE_SECONDS else "offline"
    except Exception:
        return "offline"


# ---------- §3 EMPLOYEES + §4 THREATS + §5 DEVICES: public API (MongoDB only) ----------

def connect():
    return _mongo_db()


def init_db(seed: bool = True) -> None:
    db = _mongo_db()
    db.employees.create_index("name")
    db.threat_events.create_index([("created_at", -1)])
    db.devices.create_index([("last_seen", -1)])
    if seed and db.employees.count_documents({}) == 0:
        for eid, nm, dp, rk in SEED_EMPLOYEES:
            db.employees.update_one(
                {"_id": eid},
                {"$setOnInsert": {"name": nm, "dept": dp, "risk": rk}},
                upsert=True,
            )


def list_employees() -> list:
    db = _mongo_db()
    rows = list(db.employees.find({}).sort("_id", 1))
    if not rows:
        init_db(seed=True)
        rows = list(db.employees.find({}).sort("_id", 1))
    return [_emp_doc(r) for r in rows]


def add_employee(name: str, dept: str = "", emp_id: str = "", risk: str = "low") -> dict:
    from pymongo.errors import DuplicateKeyError

    name = (name or "").strip()
    if not name:
        raise ValueError("name required")
    dept = (dept or "").strip()
    risk = (risk or "low").strip().lower() or "low"
    if risk not in ("low", "medium", "high"):
        risk = "low"
    db = _mongo_db()
    emp_id = (emp_id or "").strip()
    if not emp_id:
        nums = []
        for r in db.employees.find({"_id": {"$regex": "^E"}}, {"_id": 1}):
            try:
                nums.append(int(str(r["_id"])[1:]))
            except Exception:
                pass
        emp_id = f"E{max(nums + [3]) + 1:03d}"
    try:
        db.employees.insert_one({"_id": emp_id, "name": name, "dept": dept, "risk": risk})
    except DuplicateKeyError as exc:
        raise ValueError(f"ID {emp_id} already exists") from exc
    return {"id": emp_id, "name": name, "dept": dept, "risk": risk}


def save_threat(title: str, kind: str = "phishing", severity: str = "medium") -> dict:
    db = _mongo_db()
    doc = {"title": title, "kind": kind, "severity": severity, "created_at": _now_str()}
    res = db.threat_events.insert_one(doc)
    doc["_id"] = res.inserted_id
    return _threat_doc(doc)


def list_threats(limit: int = 20) -> list:
    db = _mongo_db()
    rows = list(db.threat_events.find({}).sort("_id", -1).limit(int(limit)))
    return [_threat_doc(r) for r in rows]


def threat_stats(limit: int = 12) -> list:
    db = _mongo_db()
    rows = list(db.threat_events.find({}, {"created_at": 1}).sort("_id", -1).limit(500))
    buckets: dict = {}
    for r in rows:
        minute = str(r.get("created_at", ""))[:16]
        if minute:
            buckets[minute] = buckets.get(minute, 0) + 1
    ordered = sorted(buckets.items())[-int(limit):]
    return [{"minute": m, "n": n} for m, n in ordered]


def set_risk(employee_id: str, risk: str) -> None:
    db = _mongo_db()
    db.employees.update_one({"_id": employee_id}, {"$set": {"risk": risk}})


def perf_summary() -> dict:
    """Overall performance: total detections + breakdown by severity/kind."""
    db = _mongo_db()
    total = db.threat_events.count_documents({})
    by_sev = {"high": 0, "medium": 0, "low": 0}
    for r in db.threat_events.aggregate([{"$group": {"_id": "$severity", "n": {"$sum": 1}}}]):
        if str(r["_id"]).lower() in by_sev:
            by_sev[str(r["_id"]).lower()] = r["n"]
    kinds = [
        {"kind": r["_id"], "n": r["n"]}
        for r in db.threat_events.aggregate(
            [{"$group": {"_id": "$kind", "n": {"$sum": 1}}}, {"$sort": {"n": -1}}, {"$limit": 6}]
        )
    ]
    return {"total": total, "by_severity": by_sev, "by_kind": kinds}


def register_device(device_id: str, employee_id: str = "", hostname: str = "", ip: str = "", os_info: str = "") -> dict:
    device_id = (device_id or "").strip()
    if not device_id:
        raise ValueError("device_id required")
    db = _mongo_db()
    db.devices.update_one(
        {"_id": device_id},
        {"$set": {
            "employee_id": (employee_id or "").strip(),
            "hostname": (hostname or "").strip(),
            "ip": (ip or "").strip(),
            "os_info": (os_info or "").strip(),
            "last_seen": _now_str(),
        }},
        upsert=True,
    )
    return get_device(device_id)


def get_device(device_id: str) -> dict:
    db = _mongo_db()
    r = db.devices.find_one({"_id": device_id})
    if not r:
        raise ValueError(f"unknown device {device_id}")
    return {
        "device_id": r["_id"],
        "employee_id": r.get("employee_id", ""),
        "hostname": r.get("hostname", ""),
        "ip": r.get("ip", ""),
        "os_info": r.get("os_info", ""),
        "last_seen": r.get("last_seen", ""),
        "conns": r.get("conns", 0),
        "status": _device_status(r.get("last_seen", "")),
    }


def device_heartbeat(device_id: str, ip: str = "", conns: int = 0) -> dict:
    db = _mongo_db()
    res = db.devices.update_one(
        {"_id": (device_id or "").strip()},
        {"$set": {"ip": (ip or "").strip(), "conns": int(conns or 0), "last_seen": _now_str()}},
    )
    if res.matched_count == 0:
        raise ValueError(f"unknown device {device_id}")
    return get_device((device_id or "").strip())


def list_devices() -> list:
    db = _mongo_db()
    rows = list(db.devices.find({}).sort("last_seen", -1).limit(200))
    out = []
    for r in rows:
        out.append({
            "device_id": r["_id"],
            "employee_id": r.get("employee_id", ""),
            "hostname": r.get("hostname", ""),
            "ip": r.get("ip", ""),
            "os_info": r.get("os_info", ""),
            "last_seen": r.get("last_seen", ""),
            "conns": r.get("conns", 0),
            "status": _device_status(r.get("last_seen", "")),
        })
    return out


if __name__ == "__main__":
    init_db(seed=True)
    print({"backend": "mongo", "employees": len(list_employees())})
