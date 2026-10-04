@echo off
REM CONTRIBUTION: One-click reproduce (no API key needed for rules/ML).
.venv\Scripts\python -m pytest tests -q
.venv\Scripts\python -m tests.eval_big
echo.
echo With key (70 LLM): .venv\Scripts\python -m tests.eval_detection
