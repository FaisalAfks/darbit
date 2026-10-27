"""The local server every darbit window, the Studio and the IDE extension talk to.

`serve()` starts it on a background thread, bound to 127.0.0.1 on a free port, and writes its port and token
to %LOCALAPPDATA%\\darbit\\server.json; a second `serve()` for the same user reuses the one that answers.
Needs the `app` extra (pip install "darbit[app]"). See docs/tasks/T05-local-server.md.
"""

import atexit
import json
import os
import secrets
import socket
import threading
import time
import urllib.error
import urllib.request
from dataclasses import asdict, dataclass

from .. import paths

STARTUP = 10.0  # seconds to wait for the server to come up


@dataclass(frozen=True)
class Running:
    port: int
    token: str
    pid: int

    @property
    def url(self) -> str:
        return f"http://127.0.0.1:{self.port}"


_server = None  # the uvicorn server this process runs, if any
_thread: threading.Thread | None = None


def info_file():
    """Where a running server writes its port and token, for windows and the IDE extension."""
    return paths.data_dir() / "server.json"


def _read_info() -> Running | None:
    try:
        data = json.loads(info_file().read_text(encoding="utf-8"))
        return Running(int(data["port"]), str(data["token"]), int(data["pid"]))
    except (OSError, ValueError, KeyError, TypeError):
        return None


def answers(server: Running) -> bool:
    """Whether a server is there and knows the token."""
    request = urllib.request.Request(f"{server.url}/ping", headers={"Authorization": f"Bearer {server.token}"})
    try:
        with urllib.request.urlopen(request, timeout=1) as response:
            return response.status == 200
    except (OSError, urllib.error.URLError):
        return False


def show_studio(server: Running) -> bool:
    """Ask the running server to bring its Studio forward. False if it has no Studio open."""
    request = urllib.request.Request(f"{server.url}/studio", headers={"Authorization": f"Bearer {server.token}"})
    try:
        with urllib.request.urlopen(request, timeout=2) as response:
            return json.loads(response.read()).get("shown") is True
    except (OSError, urllib.error.URLError, ValueError):
        return False


def running() -> Running | None:
    """The server that's running for this user, if it answers."""
    server = _read_info()
    if server is None or not answers(server):
        return None
    return server


def serve(port: int = 0) -> Running:
    """Start the server in this process on a background thread, or return the one already running."""
    global _server, _thread
    current = running()
    if current is not None:
        return current

    import uvicorn

    from .app import create_app

    token = secrets.token_urlsafe(24)
    listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    listener.bind(("127.0.0.1", port))
    chosen = listener.getsockname()[1]
    config = uvicorn.Config(
        create_app(token, chosen),
        log_level="warning",
        ws="websockets-sansio",
        ws_per_message_deflate=False,
        lifespan="off",
    )
    _server = uvicorn.Server(config)
    _thread = threading.Thread(target=_server.run, kwargs={"sockets": [listener]}, name="darbit-server", daemon=True)
    _thread.start()

    deadline = time.monotonic() + STARTUP
    while not _server.started:
        if time.monotonic() > deadline or not _thread.is_alive():
            raise RuntimeError("darbit's server didn't start")
        time.sleep(0.02)

    started = Running(chosen, token, os.getpid())
    info_file().parent.mkdir(parents=True, exist_ok=True)
    info_file().write_text(json.dumps(asdict(started)), encoding="utf-8")
    atexit.register(stop)
    return started


def stop() -> None:
    """Stop the server this process started, and forget its address."""
    global _server, _thread
    if _server is None:
        return
    mine = _read_info()
    if mine is not None and mine.pid == os.getpid():
        info_file().unlink(missing_ok=True)
    _server.should_exit = True
    if _thread is not None:
        _thread.join(timeout=STARTUP)
    _server = None
    _thread = None
