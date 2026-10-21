# T05 Local server and events

**Goal:** one small server on `127.0.0.1` that every window, the hub and the VS Code extension talk to, over one WebSocket, with screenshots sent as binary.

**Depends on:** nothing. **Issue:** #46. **Milestone:** v0.3.

## Files

- `src/darbit/server/__init__.py`: `serve()`, `running()`
- `src/darbit/server/app.py`: the Starlette app: `/ws`, `/keymap`, `/theme`, static files
- `src/darbit/server/events.py`: the in-process event bus (written as a sketch)
- `src/darbit/server/protocol.py`: every message type (written: the contract)
- `ui/src/lib/api.ts`: `connect()`, `request()`, `on()`
- `pyproject.toml`: the `ui` extra (`starlette`, `uvicorn`, `pywebview`)

## Steps

1. **Starlette + uvicorn**, not FastAPI: fewer dependencies and faster start; the API is small. Bind to `127.0.0.1` on a free port; write `{port, token, pid}` to `%LOCALAPPDATA%\darbit\server.json`. One server per user: `serve()` first checks the file and pings the server; a second start reuses it.
2. **Auth:** every request carries the token (`?token=` on the WebSocket, `Authorization: Bearer` on HTTP). Reject anything else, and any `Origin` that isn't the server's own, the Vite dev server, or `vscode-webview://`.
3. **One WebSocket** per window. Text frames are JSON: `{"type": "...", "id": 7, "data": {...}}`. A message with an `id` is a request and gets one reply with the same `id` (`{"type": "reply", "id": 7, "data": ..., "error": null}`). Messages without an `id` are events.
4. **Binary frames** for images: 4 bytes of header length, a JSON header (`{"type": "frame", "id": ..., "w": ..., "h": ..., "format": "webp"}`), then the bytes. Frozen screens are sent as lossless WebP (encode with `cv2.imencode(".webp", img, [cv2.IMWRITE_WEBP_QUALITY, 101])`); measure against PNG level 1 in T07 and keep the faster.
5. **The event bus** (`events.py`): `publish(topic, data)` from any thread, `subscribe(topic)` for the server. darbit's runtime publishes `log`, `step`, `observer`, `record` (the run report), `run.progress`; the server forwards them to subscribed windows. Publishing with no server running costs one `if`.
6. **Handlers** are plain functions registered per message type (`@handles("capture.freeze")`) in each package (`capture/service.py`, `runs/service.py`, …). They run in a thread pool so screen work never blocks the event loop.
7. **Starting it:** the desktop windows (T06) and the hub start it in-process. A bot run by `python bot.py` doesn't start it unless a tool is opened (`d.capture(...)`, `d.highlight(...)`).

## Contracts

- `protocol.py` is the list of message types and their fields. The TypeScript types in `ui/src/lib/protocol.ts` are generated from it (`python -m darbit.server.protocol --ts > ui/src/lib/protocol.ts`), so both sides can't drift.
- `server.json` location and fields: the VS Code extension reads it.

## Done when

- Two windows open; a `log` event from a running script shows in both within 50 ms.
- A 2560×1600 frame reaches a window in under 120 ms (encode + send + decode), measured and in the PR.

## Tests

- Starlette's `TestClient` WebSocket: request and reply, events, bad token rejected, bad origin rejected, a binary frame round trip.
- `events.publish` with no subscribers is a no-op and never raises.

## Not in this task

What any message does beyond `ping`, `keymap.get`, `theme.get`, `settings.get/set`.
