"""The Starlette app: one WebSocket for messages and frames, a few HTTP routes, the built UI.

Imported only when the server starts, so darbit works without the `app` extra.
See docs/tasks/T05-local-server.md.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

Handler = Callable[[dict], Any]
HANDLERS: dict[str, Handler] = {}


def handles(message: str) -> Callable[[Handler], Handler]:
    """Register the function that answers a request type from protocol.MESSAGES."""

    def register(handler: Handler) -> Handler:
        HANDLERS[message] = handler
        return handler

    return register


def create_app(token: str):  # -> starlette.applications.Starlette
    """Routes:
        /ws            messages and binary frames (token in the query)
        GET /keymap    the merged keymap (T04)
        GET /theme     the theme and custom tokens (T02)
        /              the built UI from darbit.ui.static_dir()
    Requests run their handler in a thread pool; events from darbit.server.events are forwarded to every
    socket that subscribed to their topic."""
    raise NotImplementedError("TODO(T05)")
