@echo off
REM CONTRIBUTION: Removes the endpoint agent from a PC.
REM FinLearn Guard Agent uninstaller.
schtasks /delete /tn "FinLearnGuardAgent" /f >nul 2>nul
taskkill /f /im pythonw.exe /fi "WINDOWTITLE eq agent.py" >nul 2>nul
echo [OK] Agent task removed. You can delete this folder.
pause
