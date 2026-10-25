"""The in-process event bus: darbit's runtime publishes, the local server forwards to windows.

    events.publish("log", {"line": "found Gui.Play"})       # from any thread; free when nobody listens

See docs/tasks/T05-local-server.md.
"""

import threading
from collections.abc import Callable

Listener = Callable[[str, dict], None]

_listeners: list[Listener] = []
_lock = threading.Lock()


def listen(listener: Listener) -> Callable[[], None]:
    """Get every event from now on. Returns a function that stops listening."""
    with _lock:
        _listeners.append(listener)

    def stop() -> None:
        with _lock:
            if listener in _listeners:
                _listeners.remove(listener)

    return stop


def publish(topic: str, data: dict) -> None:
    """Send an event to every listener. Never raises; a broken listener is skipped."""
    if not _listeners:
        return
    with _lock:
        listeners = list(_listeners)
    for listener in listeners:
        try:
            listener(topic, data)
        except Exception:  # noqa: BLE001, S112 - one window's problem must not stop the script
            continue
