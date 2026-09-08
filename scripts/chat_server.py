#!/usr/bin/env python3
"""Chat server voor Portal Dominicano (Radio Dominicana).

WebSocket chat met kamers. Draait lokaal, geen Docker nodig.
- GET  /              -> status
- WS   /ws?room=X     -> chat kamer (default "radio")
- Bewaart laatste 100 berichten per kamer in geheugen.

Start: python3 chat_server.py [poort]  (default 8765)
"""
import asyncio
import json
import sys
import time

import websockets

PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8765

# kamer -> lijst van {user, text, ts}
HISTORY = {}
MAX_MSGS = 100

# kamer -> set van websockets
ROOMS = {}


def room_history(room):
    return HISTORY.setdefault(room, [])


async def broadcast(room, msg):
    hs = room_history(room)
    hs.append(msg)
    if len(hs) > MAX_MSGS:
        del hs[: len(hs) - MAX_MSGS]
    if room in ROOMS:
        dead = []
        for ws in ROOMS[room]:
            try:
                await ws.send(json.dumps({"type": "msg", **msg}))
            except Exception:
                dead.append(ws)
        for ws in dead:
            ROOMS[room].discard(ws)


async def handler(ws):
    # parse kamer uit query
    room = "radio"
    try:
        path = ws.request.path if hasattr(ws, "request") else ws.path
        if "?" in path:
            q = path.split("?", 1)[1]
            for kv in q.split("&"):
                if kv.startswith("room="):
                    room = kv.split("=", 1)[1] or "radio"
    except Exception:
        room = "radio"

    ROOMS.setdefault(room, set()).add(ws)
    try:
        # stuur historie bij binnenkomst
        for m in room_history(room)[-50:]:
            await ws.send(json.dumps({"type": "msg", **m}))

        async for raw in ws:
            try:
                data = json.loads(raw)
            except Exception:
                continue
            user = (data.get("user") or "Anónimo").strip()[:24]
            text = (data.get("text") or "").strip()
            if not text or len(text) > 400:
                continue
            await broadcast(room, {"user": user, "text": text, "ts": time.time()})
    except websockets.ConnectionClosed:
        pass
    finally:
        ROOMS[room].discard(ws)


async def main():
    async with websockets.serve(handler, "0.0.0.0", PORT, max_size=2 ** 20):
        print(f"Chat server draait op poort {PORT} (ws://0.0.0.0:{PORT}/ws)")
        await asyncio.Future()  # run forever


if __name__ == "__main__":
    asyncio.run(main())
