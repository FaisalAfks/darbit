"""Low-level keyboard and mouse hooks, for the recorder. See docs/tasks/T15-recorder.md.

WH_KEYBOARD_LL and WH_MOUSE_LL on their own thread with a message loop. The callbacks only put
events on a queue and return at once; injected events (darbit's own input) are skipped.
"""

from __future__ import annotations

from collections.abc import Callable


def start(on_event: Callable[[str, str, int, int, int], None]) -> Callable[[], None]:
    """Start the hooks; on_event(kind, key, x, y, time_ns) is called from the hook thread's queue reader.
    Returns a function that removes the hooks."""
    raise NotImplementedError("TODO(T15)")
