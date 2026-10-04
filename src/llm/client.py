# CONTRIBUTION: Single OpenRouter caller shared by every agent.
"""Single OpenRouter gateway for ALL agents. No dummy fallbacks.

SECTIONS:
  §1 KEY   - OPENROUTER_API_KEY from .env (error tells where to get one)
  §2 MODEL - free model name from .env (default ministral-8b)
  §3 CALL   - one chat request -> assistant text (agents parse JSON out of it)

Agents must surface the missing-key message instead of inventing placeholder text.
"""
import os

import httpx
from dotenv import load_dotenv

load_dotenv()

API_URL = "https://openrouter.ai/api/v1/chat/completions"


# ---------- §1 KEY: read OPENROUTER_API_KEY from .env (error tells where to get one) ----------
def get_key() -> str:
    key = os.getenv("OPENROUTER_API_KEY", "").strip()
    if not key:
        raise RuntimeError(
            "OPENROUTER_API_KEY not set. Get one at https://openrouter.ai/keys "
            "then add OPENROUTER_API_KEY=sk-or-v1-... to E:\\finlearn-guard-final\\.env"
        )
    return key


# ---------- §2 MODEL: free model name from .env (default ministral-8b) ----------
def get_model() -> str:
    return os.getenv("OPENROUTER_MODEL", "mistralai/ministral-8b-2512").strip()


# ---------- §3 CALL: one chat request -> assistant text (agents parse JSON out of it) ----------
def generate(prompt: str, system: str = "You are a helpful assistant.", timeout: int = 60) -> str:
    key = get_key()
    resp = httpx.post(
        API_URL,
        headers={"Authorization": f"Bearer {key}"},
        json={
            "model": get_model(),
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": prompt},
            ],
        },
        timeout=timeout,
    )
    resp.raise_for_status()
    data = resp.json()
    return data["choices"][0]["message"]["content"]
