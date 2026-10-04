# CONTRIBUTION: Endpoint agent: watches PC connections and reports bursts to the server.
"""FinLearn Guard endpoint agent (stdlib only, no pip packages needed).

Runs on a monitored Windows PC. Every INTERVAL seconds it:
  1. Registers itself with the central server (first run / on config change)
  2. Takes a network snapshot (local IPs, active TCP connection count,
     top remote hosts via `netstat -ano`)
  3. POSTs a heartbeat to /api/devices/heartbeat
  4. If something looks suspicious (many distinct remote hosts or a
     connection burst), POSTs an event to /api/threats so the website's
     detector + live feed + risk bump handle it like any other threat.

Config lives next to this file in config.json (created by install.bat):
  {"server_url": "http://SERVER-IP:8000", "device_id": "",
   "employee_id": "E001", "interval": 30}
Blank device_id = auto-generated once from hostname and saved back.
"""
import json
import platform
import re
import socket
import subprocess
import time
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
CONFIG = HERE / "config.json"

# ---------- CONFIG: server address + IDs + interval (created by install.bat) ----------
DEFAULTS = {
    "server_url": "http://127.0.0.1:8000",
    "device_id": "",
    "employee_id": "",
    "interval": 30,
}


def load_config() -> dict:
    cfg = dict(DEFAULTS)
    if CONFIG.exists():
        try:
            cfg.update(json.loads(CONFIG.read_text()))
        except Exception:
            pass
    cfg["server_url"] = str(cfg.get("server_url", "")).rstrip("/")
    if not cfg.get("device_id"):
        cfg["device_id"] = f"{platform.node()}-{abs(hash(socket.gethostname())) % 9000 + 1000}"
        save_config(cfg)
    return cfg


def save_config(cfg: dict) -> None:
    try:
        CONFIG.write_text(json.dumps(cfg, indent=2))
    except Exception:
        pass


# ---------- HTTP: tiny POST helper (stdlib only, no pip packages) ----------
def post(url: str, payload: dict, timeout: int = 10) -> dict:
    data = json.dumps(payload).encode()
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode() or "{}")


# ---------- SNAPSHOT: local IPs (ipconfig) + TCP picture (netstat) ----------
def local_ips() -> list:
    ips = set()
    try:
        ips.add(socket.gethostbyname(socket.gethostname()))
    except Exception:
        pass
    try:
        out = subprocess.run(["ipconfig"], capture_output=True, text=True, timeout=10).stdout
        for m in re.findall(r"IPv4 Address[^\d]*([\d.]+)", out):
            if not m.startswith("127."):
                ips.add(m)
    except Exception:
        pass
    return sorted(ips)


def netstat_snapshot() -> dict:
    """Parse `netstat -ano` (TCP only): connection count + top remote hosts."""
    conns = 0
    hosts: dict = {}
    try:
        out = subprocess.run(["netstat", "-ano", "-p", "TCP"], capture_output=True, text=True, timeout=15).stdout
        for line in out.splitlines():
            parts = line.split()
            if len(parts) >= 4 and parts[0].upper() == "TCP":
                remote = parts[2].rsplit(":", 1)[0]
                if remote and not remote.startswith("127.") and remote != "0.0.0.0":
                    conns += 1
                    hosts[remote] = hosts.get(remote, 0) + 1
    except Exception:
        pass
    top = sorted(hosts.items(), key=lambda kv: kv[1], reverse=True)[:8]
    return {"conns": conns, "distinct": len(hosts), "top": [{"host": h, "n": n} for h, n in top]}


# ---------- MAIN LOOP: register once, then heartbeat + suspicion report forever ----------
def main() -> None:
    cfg = load_config()
    server = cfg["server_url"]
    device_id = cfg["device_id"]
    employee_id = cfg.get("employee_id", "")
    interval = max(10, int(cfg.get("interval", 30)))

    hostname = platform.node()
    os_info = f"{platform.system()} {platform.release()} ({platform.version()})"
    ips = local_ips()
    try:
        post(f"{server}/api/devices/register", {
            "device_id": device_id,
            "employee_id": employee_id,
            "hostname": hostname,
            "ip": ips[0] if ips else "",
            "os_info": os_info[:120],
        })
    except Exception as exc:
        print(f"register failed: {exc}", flush=True)

    while True:
        try:
            ips = local_ips()
            snap = netstat_snapshot()
            post(f"{server}/api/devices/heartbeat", {
                "device_id": device_id,
                "ip": ips[0] if ips else "",
                "conns": snap["conns"],
            })
            # Suspicion heuristics: burst or spray -> let the server analyze.
            if snap["distinct"] >= 40 or snap["conns"] >= 120:
                try:
                    top = ", ".join(f"{t['host']}x{t['n']}" for t in snap["top"][:4])
                    post(f"{server}/api/threats", {
                        "title": f"Agent {device_id}: {snap['conns']} conns / {snap['distinct']} hosts ({top})",
                        "kind": "network",
                        "body": f"host={hostname} ip={ips[0] if ips else ''} conns={snap['conns']} distinct={snap['distinct']}",
                        "employee_id": employee_id,
                    })
                except Exception:
                    pass
        except Exception as exc:
            print(f"loop error: {exc}", flush=True)
        time.sleep(interval)


if __name__ == "__main__":
    main()
