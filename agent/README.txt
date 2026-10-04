CONTRIBUTION: How to install the endpoint agent on another PC.

FinLearn Guard Agent - install on the PC you want to monitor.
=====================================================
Needs: Windows 10/11 + Python 3.10+ (python.org). No pip packages.

INSTALL (on the target device):
  1. Copy this whole `agent` folder to the device (USB / share).
     Put it at  C:\FinLearnAgent\  (recommended).
  2. Double-click install.bat
     - asks for SERVER address  (the PC running the website,
       e.g. http://192.168.1.10:8000  - NOT 127.0.0.1 from another PC)
     - asks for employee ID    (e.g. E001 - see All Users page)
     - registers the device, creates auto-start task, starts monitoring.
  3. On the website open /devices - the PC shows online (green).

WHAT IT DOES (every 30s, configurable):
  - heartbeat: hostname, IP, active TCP count -> /api/devices/heartbeat
  - anomaly: 120+ connections OR 40+ distinct remote hosts ->
             posts to /api/threats -> detector + live feed + risk bump.
  - No packet capture, no keystrokes, no files - connection counts only.

UNINSTALL: run uninstall.bat (stops task, removes autorun; folder can be deleted).
TROUBLESHOOT:
  - Device stuck offline: target PC must reach SERVER:8000
    (test in browser on target PC: http://SERVER-IP:8000/health).
  - Firewall: allow inbound TCP 8000 on the SERVER PC.
  - Logs: task runs hidden; run `python agent.py` manually to see errors.
