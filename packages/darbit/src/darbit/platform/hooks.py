"""Real keyboard and mouse input for the recorder and the run pill, through the system's Listener piece.

`start(on_event)` gets every real key and mouse button change as `on_event(kind, code, x, y, time_ns)`; input a
program sends (darbit's own clicks and keys) is left out. platform/win32/listener.py lists the kinds.
"""

from collections.abc import Callable

from . import backend

OnEvent = Callable[[str, int, int, int, int], None]  # kind, code, x, y, time_ns


def start(on_event: OnEvent, moves: bool = False) -> Callable[[], None]:
    """Get every real key and mouse button change (and cursor moves with `moves`). Returns a function that stops it."""
    return backend.listener().start(on_event, moves)


def watch_mouse(on_move: Callable[[int, int], None]) -> Callable[[], None]:
    """Call on_move(x, y) for every real mouse move, in screen pixels. Returns a function that stops it."""
    return backend.listener().watch_mouse(on_move)
