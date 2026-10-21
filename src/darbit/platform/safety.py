"""The stop hotkey, a sleep it can cut short, and keeping the PC awake.

A small thread watches the keyboard. When the stop hotkey is pressed, every held key
and button is let go, and every darbit call from then on raises Stopped, including
a sleep that's already running.
"""
from __future__ import annotations

import atexit
import ctypes
import threading
import time
from collections.abc import Callable

from ..errors import Stopped
from .keys import key

_stopped = threading.Event()
_on_stop: list[Callable[[], None]] = []
_watching: str | None = None


def on_stop(callback: Callable[[], None]) -> None:
    """Run `callback` the moment the stop hotkey is pressed."""
    _on_stop.append(callback)


def stop() -> None:
    """Do what the stop hotkey does."""
    if _stopped.is_set():
        return
    _stopped.set()
    for callback in _on_stop:
        callback()


def check() -> None:
    """Raise Stopped if the stop hotkey was pressed."""
    if _stopped.is_set():
        raise Stopped("stopped by the stop hotkey")


def sleep(seconds: float) -> None:
    """Wait, but stop at once when the stop hotkey is pressed."""
    if seconds > 0 and _stopped.wait(seconds):
        check()
    check()


def watch(combo: str) -> None:
    """Start watching for the stop hotkey, e.g. "ctrl+alt+q". Calling it again with a new combo switches to it."""
    global _watching
    first = _watching is None
    vks = tuple(key(part).vk for part in combo.split("+"))
    _watching = combo
    if not first:
        _watch_keys[0] = vks
        return
    _watch_keys[0] = vks
    get_state = ctypes.windll.user32.GetAsyncKeyState
    get_state.argtypes = (ctypes.c_int,)
    get_state.restype = ctypes.c_short

    def run() -> None:
        while True:
            if all(get_state(vk) & 0x8000 for vk in _watch_keys[0]):
                stop()
            time.sleep(0.05)

    threading.Thread(target=run, name="darbit-stop-key", daemon=True).start()


_watch_keys: list[tuple[int, ...]] = [()]

# keeping the PC awake
_ES_CONTINUOUS, _ES_SYSTEM_REQUIRED, _ES_DISPLAY_REQUIRED = 0x80000000, 0x00000001, 0x00000002


def keep_awake() -> None:
    """Stop Windows from sleeping or turning the screen off until the script ends."""
    try:
        ctypes.windll.kernel32.SetThreadExecutionState(_ES_CONTINUOUS | _ES_SYSTEM_REQUIRED | _ES_DISPLAY_REQUIRED)
        atexit.register(lambda: ctypes.windll.kernel32.SetThreadExecutionState(_ES_CONTINUOUS))
    except (AttributeError, OSError):
        pass
