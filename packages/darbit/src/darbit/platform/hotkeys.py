"""Global shortcuts that work with any window in front, through the system's Hotkeys piece."""

from collections.abc import Callable

from . import backend


def register(keys: dict[str, str], handlers: dict[str, Callable[[], None]]) -> object:
    """Register each action's keys; pressing them calls its handler. Returns what to `stop()`, with the actions
    the system refused in `missing`."""
    return backend.hotkeys().register(keys, handlers)
