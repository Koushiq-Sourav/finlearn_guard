@echo off
REM CONTRIBUTION: Double-click to start the class demo server on :8000.
REM FinLearn Guard - LOCAL LIVE run (double-click this)
cd /d %~dp0..
.\.venv\Scripts\python.exe -m uvicorn src.main:app --host 127.0.0.1 --port 8000
pause
