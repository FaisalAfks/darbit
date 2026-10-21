"""The stop hotkey, interrupts from observers, a sleep they can cut short, and keeping the PC awake.

A small thread watches the keyboard. When the stop hotkey is pressed, every held key
and button is let go, and every darbit call from then on raises Stopped, including
a sleep that's already running.

An observer that fires posts an interrupt: held keys are let go and the next darbit
call in the script's main thread raises Interrupted, once.
"""
from __future__ import annotations

import atexit
import ctypes
import threading
import time
from collections.abc import Callable

from ..errors import Interrupted, Stopped
from .keys import key

_stopped = threading.Event()
_wake = threading.Event()  # set by a stop or an interrupt, to cut a sleep short
_on_stop: list[Callable[[], None]] = []
_pending: list[Interrupted] = []  # at most one interrupt waiting for the script
_lock = threading.Lock()
_muted = 0  # inside no_interrupts() blocks
_watching: str | None = None
_armed = False


def on_stop(callback: Callable[[], None]) -> None:
    """Run `callback` the moment the stop hotkey is pressed."""
    _on_stop.append(callback)


def stop() -> None:
    """Do what the stop hotkey does."""
    if _stopped.is_set():
        return
    _stopped.set()
    _wake.set()
    for callback in _on_stop:
        callback()


def interrupt(event: Interrupted) -> bool:
    """Post an interrupt for the script. False if one is already waiting or interrupts are muted."""
    with _lock:
        if _pending or _muted:
            return False
        _pending.append(event)
    _wake.set()
    return True


def _take_interrupt() -> None:
    if threading.current_thread() is not threading.main_thread():
        return
    with _lock:
        if not _pending or _muted:
            return
        event = _pending.pop()
        if not _stopped.is_set():
            _wake.clear()
    for callback in _on_stop:  # let go of held keys and buttons, as for a stop
        callback()
    raise event


class _NoInterrupts:
    def __enter__(self) -> None:
        global _muted
        with _lock:
            _muted += 1

    def __exit__(self, *exc: object) -> None:
        global _muted
        with _lock:
            _muted -= 1


def no_interrupts() -> _NoInterrupts:
    """A block where observers don't interrupt the script, e.g. while it recovers from an interrupt."""
    return _NoInterrupts()


def arm() -> None:
    """Start the stop hotkey and keep the PC awake, once. Called by the first darbit call that can be stopped,
    so importing darbit (e.g. for the capture tool) starts no thread."""
    global _armed
    if _armed:
        return
    _armed = True
    from ..settings import settings

    watch(settings.stop_key)
    keep_awake()


def check() -> None:
    """Raise Stopped if the stop hotkey was pressed."""
    arm()
    if _stopped.is_set():
        raise Stopped("stopped by the stop hotkey")
    _take_interrupt()


def sleep(seconds: float) -> None:
    """Wait, but stop at once when the stop hotkey is pressed or an observer interrupts."""
    check()
    deadline = time.monotonic() + seconds
    while (left := deadline - time.monotonic()) > 0:
        if not _wake.wait(left):
            break
        check()  # raises for a stop, or for an interrupt in the main thread
        _stopped.wait(max(0.0, deadline - time.monotonic()))  # an interrupt meant for another thread: sleep on
        break
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
