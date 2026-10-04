# CONTRIBUTION: Renders step-by-step mp4 guides, else honest slide cards.
"""Free video layer: moviepy slide-video if available, else HTML slides.

make_guide_video(steps, title) -> {"video_url": "/media/x.mp4" | None, "slides": [...], "video_error": str|None}
No fake files: if moviepy/ffmpeg is missing we return slides only (the UI
renders them as step cards) + a clear video_error. Never a placeholder mp4.
"""
import hashlib
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
MEDIA_DIR = BASE_DIR / "data" / "media"


# ---------- PATHS: one cached mp4 per unique (title + steps) ----------
def _path_for(title: str, steps: list) -> Path:
    MEDIA_DIR.mkdir(parents=True, exist_ok=True)
    h = hashlib.sha256((title + "|" + "|".join(steps)).encode("utf-8")).hexdigest()[:16]
    return MEDIA_DIR / f"guide-{h}.mp4"


# ---------- GUIDE VIDEO: slide mp4 if moviepy+ffmpeg exist, else slides-only (never fake) ----------
def make_guide_video(steps: list, title: str = "Fix guide") -> dict:
    slides = [{"n": i + 1, "text": str(s)[:140]} for i, s in enumerate(steps[:5])]
    out = _path_for(title, [str(s) for s in steps])
    if out.exists() and out.stat().st_size > 5000:
        return {"video_url": f"/media/{out.name}", "slides": slides, "video_error": None}
    try:
        import moviepy  # noqa: F401  (pip install moviepy, needs ffmpeg)
    except ImportError:
        return {
            "video_url": None,
            "slides": slides,
            "video_error": "Video file needs moviepy (pip install moviepy + ffmpeg). Step cards below work without it.",
        }
    try:
        from moviepy import ColorClip, TextClip, CompositeVideoClip, concatenate_videoclips

        clips = []
        for i, s in enumerate(steps[:5]):
            bg = ColorClip(size=(640, 360), color=(10, 25, 48), duration=2.0)
            try:
                txt = TextClip(
                    text=f"Step {i + 1}: {s}"[:120],
                    font_size=28, color="white", size=(560, 300), method="caption",
                ).with_position("center").with_duration(2.0)
                clips.append(CompositeVideoClip([bg, txt]))
            except Exception:
                clips.append(bg)
        if not clips:
            return {"video_url": None, "slides": slides, "video_error": "No steps to render."}
        concatenate_videoclips(clips).write_videofile(str(out), fps=12, logger=None)
    except Exception as exc:
        return {"video_url": None, "slides": slides, "video_error": f"Video render failed: {exc!s}"[:150]}
    if out.exists() and out.stat().st_size > 5000:
        return {"video_url": f"/media/{out.name}", "slides": slides, "video_error": None}
    return {"video_url": None, "slides": slides, "video_error": "Video render produced no file."}
