@echo off
REM CONTRIBUTION: One-click setup that creates agent config on a new PC.
REM FinLearn Guard Agent installer - run on the TARGET pc (right-click: Run as administrator recommended).
setlocal
cd /d "%~dp0"

where python >nul 2>nul
if errorlevel 1 (
  echo [ERROR] Python not found. Install Python 3.10+ from https://www.python.org/downloads/ first.
  pause
  exit /b 1
)

set /p SERVER="Server address (e.g. http://192.168.1.10:8000): "
if "%SERVER%"=="" set SERVER=http://127.0.0.1:8000
set /p EMP="Employee ID for this PC (e.g. E001, blank = none): "

python -c "import json; p='config.json'; c=json.load(open(p)); c['server_url']='%SERVER%'; c['employee_id']='%EMP%'; json.dump(c, open(p,'w'), indent=2); print('config saved:', c['server_url'], '|', c['employee_id'] or '(no user)')"

REM quick connectivity check (register once, 15s timeout)
python -c "import json,urllib.request,socket,platform; c=json.load(open('config.json')); d={'device_id':platform.node(),'employee_id':c.get('employee_id',''),'hostname':platform.node(),'ip':'','os_info':platform.system()}; r=urllib.request.Request(c['server_url']+'/api/devices/register', data=json.dumps(d).encode(), headers={'Content-Type':'application/json'}); print('server:', json.load(urllib.request.urlopen(r, timeout=15)).get('ok'))"

set TASKPY=%~dp0agent.py
schtasks /create /tn "FinLearnGuardAgent" /tr "pythonw.exe \"%TASKPY%\"" /sc onlogon /rl limited /f
schtasks /run /tn "FinLearnGuardAgent" >nul 2>nul

echo.
echo [OK] Installed. Agent starts at every logon and is running now.
echo Check the website Devices page: %SERVER%/devices
pause
