# CONTRIBUTION: Renders spoken mp3 guides via free edge-tts.
"""Free voice layer: edge-tts (Microsoft, no key, 2-4 sec).

speak(text) -> data/media/<hash>.mp3 (returns /media/<file> URL path).
No fake files: if edge-tts is missing or net fails, raises RuntimeError
with the exact fix (pip install edge-tts). Callers surface it as audio_error.
"""
import asyncio
import hashlib
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
MEDIA_DIR = BASE_DIR / "data" / "media"
VOICE = "en-US-AriaNeural"  # free Microsoft voice (no key, 2-4 sec per guide)


# ---------- PATHS: one cached mp3 per unique text (same text = no re-render) ----------
def _path_for(text: str) -> Path:
    MEDIA_DIR.mkdir(parents=True, exist_ok=True)
    h = hashlib.sha256(text.strip().encode("utf-8")).hexdigest()[:16]
    return MEDIA_DIR / f"voice-{h}.mp3"


# ---------- RENDER: text -> mp3 via edge-tts (async) ----------
async def _render(text: str, out: Path) -> None:
    import edge_tts  # pip install edge-tts (free, no key)

    await edge_tts.Communicate(text.strip()[:600], VOICE).save(str(out))


# ---------- SPEAK: cached render; isolates its own event loop (FastAPI-safe) ----------
def speak(text: str) -> str:
    """Render text to mp3, return URL path /media/<file>. Cached by hash."""
    import asyncio as _aio

    out = _path_for(text)
    if out.exists() and out.stat().st_size > 1000:
        return f"/media/{out.name}"

    def _run() -> None:
        _aio.run(_render(text, out))

    try:
        _aio.get_running_loop()
        running = True
    except RuntimeError:
        running = False
    try:
        if running:
            import concurrent.futures as _cf

            with _cf.ThreadPoolExecutor(max_workers=1) as pool:
                pool.submit(_run).result(timeout=90)
        else:
            _run()
    except ImportError:
        raise RuntimeError("edge-tts not installed. Run: .\\.venv\\Scripts\\pip.exe install edge-tts")
    if not out.exists() or out.stat().st_size < 1000:
        raise RuntimeError("Voice render failed (no network?). Text guide still works below.")
    return f"/media/{out.name}"
