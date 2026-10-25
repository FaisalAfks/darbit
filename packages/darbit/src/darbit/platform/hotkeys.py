"""Global hotkeys from the keymap's [global] scope. See docs/tasks/T04-keymap.md.

RegisterHotKey on one thread with its own message loop. The stop key always works: if the
keymap can't be read, it falls back to ctrl+alt+q.
"""

from __future__ import annotations

from collections.abc import Callable


def register(keys: dict[str, str], handlers: dict[str, Callable[[], None]]) -> Callable[[], None]:
    """Register each action's keys; pressing them calls its handler. Returns a function that unregisters."""
    raise NotImplementedError("TODO(T04)")
