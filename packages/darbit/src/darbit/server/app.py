"""The Starlette app: one WebSocket for messages and frames, a few HTTP routes, the built UI.

Imported only when the server starts, so darbit works without the `app` extra. Each window opens one
WebSocket with the server's token; a message with an `id` is a request and gets one reply, a message
without one is an event. Handlers are plain functions (`@handles("ping")`) run in a thread pool, so
screen work never blocks the other windows. See docs/tasks/T05-local-server.md.
"""

import asyncio
import json
from collections.abc import Callable
from typing import Any

from starlette.applications import Starlette
from starlette.concurrency import run_in_threadpool
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Mount, Route, WebSocketRoute
from starlette.staticfiles import StaticFiles
from starlette.websockets import WebSocket, WebSocketDisconnect

from .. import __version__, keymap
from . import ui_settings
from .events import listen, publish
from .frames import Frame, pack

Handler = Callable[[dict], Any]
HANDLERS: dict[str, Handler] = {}

DEV_ORIGINS = ("http://127.0.0.1:5173", "http://localhost:5173")  # the Vite dev server (DARBIT_UI_DEV=1)
POLICY_VIOLATION = 1008  # WebSocket close code for a bad token or origin


def handles(message: str) -> Callable[[Handler], Handler]:
    """Register the function that answers a request type from protocol.MESSAGES."""

    def register(handler: Handler) -> Handler:
        HANDLERS[message] = handler
        return handler

    return register


# ---- the requests every window can make (T05); the tools register theirs in their own packages


@handles("ping")
def ping(data: dict) -> dict:
    return {"darbit": __version__}


@handles("keymap.get")
def keymap_get(data: dict) -> dict:
    return keymap.load()


@handles("theme.get")
def theme_get(data: dict) -> dict:
    return ui_settings.theme()


@handles("settings.get")
def settings_get(data: dict) -> object:
    return ui_settings.get(str(data.get("key", "")))


@handles("settings.set")
def settings_set(data: dict) -> None:
    key = str(data.get("key", ""))
    if not key:
        raise ValueError("settings.set needs a key")
    ui_settings.set_value(key, data.get("value"))
    if key == "ui.theme":
        publish("theme.changed", ui_settings.theme())  # every window switches together


# ---- checks


def origin_allowed(origin: str | None, port: int) -> bool:
    """The server's own pages, the Vite dev server, VS Code webviews, and programs (no Origin)."""
    if origin is None:
        return True
    own = (f"http://127.0.0.1:{port}", f"http://localhost:{port}")
    if origin in own or origin in DEV_ORIGINS:
        return True
    return origin.startswith("vscode-webview://")


def token_given(request: Request, token: str) -> bool:
    if request.query_params.get("token") == token:
        return True
    return request.headers.get("authorization") == f"Bearer {token}"


# ---- one window's connection


class Connection:
    """A window's WebSocket: answers its requests and forwards every event to it."""

    def __init__(self, socket: WebSocket) -> None:
        self.socket = socket
        self.sending = asyncio.Lock()  # one message at a time, so frames never interleave

    async def send_text(self, message: dict) -> None:
        async with self.sending:
            await self.socket.send_text(json.dumps(message, default=str))

    async def send_frame(self, frame: Frame, request: int | None) -> None:
        async with self.sending:
            await self.socket.send_bytes(pack(frame.header(request), frame.data))

    async def answer(self, text: str) -> None:
        try:
            message = json.loads(text)
        except ValueError:
            return
        kind = message.get("type")
        request = message.get("id")
        if request is None:
            return  # an event from a window: nothing listens to those yet
        handler = HANDLERS.get(kind)
        if handler is None:
            await self.send_text({"type": "reply", "id": request, "data": None, "error": f"unknown request {kind!r}"})
            return
        try:
            result = await run_in_threadpool(handler, message.get("data") or {})
        except Exception as error:  # noqa: BLE001 - the window gets the reason instead of a hang
            await self.send_text({"type": "reply", "id": request, "data": None, "error": str(error)})
            return
        if isinstance(result, Frame):
            await self.send_frame(result, request)
            result = {"frame": True, "w": result.w, "h": result.h}
        await self.send_text({"type": "reply", "id": request, "data": result, "error": None})

    async def forward(self, queue: asyncio.Queue) -> None:
        while True:
            topic, data = await queue.get()
            if isinstance(data, Frame):
                await self.send_frame(data, None)
            else:
                await self.send_text({"type": topic, "data": data})


def create_app(token: str, port: int = 0) -> Starlette:
    """Routes:
    /ws            messages and binary frames (token in the query)
    GET /ping      is it there (token as a Bearer header or in the query)
    GET /keymap    the merged keymap (T04)
    GET /theme     the theme and custom tokens (T02)
    /              the built UI from darbit.ui.static_dir(), when it's there
    """

    async def websocket(socket: WebSocket) -> None:
        good_token = socket.query_params.get("token") == token
        if not good_token or not origin_allowed(socket.headers.get("origin"), port):
            await socket.close(code=POLICY_VIOLATION)
            return
        await socket.accept()
        connection = Connection(socket)
        loop = asyncio.get_running_loop()
        queue: asyncio.Queue = asyncio.Queue()

        def on_event(topic: str, data: dict) -> None:
            loop.call_soon_threadsafe(queue.put_nowait, (topic, data))

        stop_listening = listen(on_event)
        forwarding = asyncio.create_task(connection.forward(queue))
        answering: set[asyncio.Task] = set()
        try:
            while True:
                text = await socket.receive_text()
                task = asyncio.create_task(connection.answer(text))  # a slow request doesn't hold up the next
                answering.add(task)
                task.add_done_callback(answering.discard)
        except WebSocketDisconnect:
            pass
        finally:
            stop_listening()
            forwarding.cancel()
            for task in answering:
                task.cancel()

    def guarded(handler: Handler) -> Callable[[Request], Any]:
        async def endpoint(request: Request) -> JSONResponse:
            if not token_given(request, token):
                return JSONResponse({"error": "token needed"}, status_code=401)
            return JSONResponse(await run_in_threadpool(handler, {}))

        return endpoint

    routes = [
        WebSocketRoute("/ws", websocket),
        Route("/ping", guarded(ping)),
        Route("/keymap", guarded(keymap_get)),
        Route("/theme", guarded(theme_get)),
    ]
    from ..ui import static_dir
    from . import actions_api, capture_api, hub, record_api

    hub.register()
    capture_api.register()
    actions_api.register()
    record_api.register()

    static = static_dir()
    if static.is_dir():
        routes.append(Mount("/", StaticFiles(directory=static, html=True)))  # the pages hold no secrets
    return Starlette(routes=routes)
