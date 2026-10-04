# CONTRIBUTION: Live hub pushing every alert to open browsers instantly.
"""LIVE ALERT HUB (WebSocket): dashboard shows LIVE while connected here.
T2 plugs the detector broadcast into `broadcast()`.

SECTIONS:
  SUBSCRIBERS - the set of currently connected browsers
  SEND        - push one message to one browser (never crashes)
  BROADCAST   - push one message to ALL browsers, drop dead ones
  HANDLER     - per-browser loop: hello on connect, ping every 30s idle
"""
import asyncio
import json

# ---------- SUBSCRIBERS: all browsers currently watching the feed ----------
_subscribers: set = set()


# ---------- SEND: one message -> one browser ----------
async def _send(ws, msg: dict) -> None:
    try:
        await ws.send_text(json.dumps(msg))
    except Exception:
        pass


# ---------- BROADCAST: one message -> every browser ----------
async def broadcast(msg: dict) -> None:
    dead = []
    for ws in list(_subscribers):
        try:
            await ws.send_text(json.dumps(msg))
        except Exception:
            dead.append(ws)
    for ws in dead:
        _subscribers.discard(ws)


# ---------- HANDLER: lifetime of one browser connection ----------
async def handler(websocket) -> None:
    await websocket.accept()
    _subscribers.add(websocket)
    try:
        await _send(websocket, {"type": "hello", "msg": "live feed connected"})
        while True:
            try:
                await asyncio.wait_for(websocket.receive_text(), timeout=30)
            except asyncio.TimeoutError:
                await _send(websocket, {"type": "ping"})
    except Exception:
        pass
    finally:
        _subscribers.discard(websocket)
