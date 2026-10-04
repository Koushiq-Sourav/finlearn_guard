#!/bin/sh
# CONTRIBUTION: One-click reproduce (no API key needed for rules/ML).
python3 -m pytest tests -q
python3 -m tests.eval_big
echo "With key (70 LLM): python3 -m tests.eval_detection"
