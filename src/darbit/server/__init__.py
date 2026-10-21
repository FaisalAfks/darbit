"""The local server every darbit window, the hub and the IDE extension talk to.

Needs the `ui` extra (pip install "darbit[ui]"). See docs/tasks/T05-local-server.md.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Running:
    port: int
    token: str
    pid: int


def info_file() -> Path:
    """Where a running server writes its port and token, for windows and the IDE extension."""
    return Path(os.environ.get("LOCALAPPDATA", Path.home())) / "darbit" / "server.json"


def running() -> Running | None:
    """The server that's running for this user, if it answers."""
    raise NotImplementedError("TODO(T05): read info_file() and ping it")


def serve(port: int = 0) -> Running:
    """Start the server in this process on a background thread, or return the one already running."""
    raise NotImplementedError("TODO(T05): Starlette app from server.app on uvicorn, bound to 127.0.0.1")
