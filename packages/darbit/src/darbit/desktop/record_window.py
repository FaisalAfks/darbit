"""Recording from darbit Studio: hide the Studio, show the recorder bar at the top, record, then open the action.

The bar is a `bar` window (on top, never takes focus) at the top centre of the Studio's screen. Its live
steps panel makes it taller (`record.size`). Ctrl+Alt+P pauses and Ctrl+Alt+R stops, from the keymap's
[global] keys. Decision 0013, round 8.
"""

import threading
from pathlib import Path

from .. import keymap
from ..platform import hotkeys
from ..server import record_api
from ..server.events import publish
from . import pill
from .windows import Window, open_window

BAR_WIDTH = 620  # px, the bar and its panels
BAR_HEIGHT = 76
PANEL_HEIGHT = 470  # with the check menu or the live steps open


def _keys() -> dict[str, str]:
    try:
        found = keymap.defaults()["global"]
    except (KeyError, OSError, ValueError):
        found = {}
    return {
        "run.pause": found.get("run.pause", "ctrl+alt+p"),
        "record.toggle": found.get("record.toggle", "ctrl+alt+r"),
    }


class RecordWindow:
    def __init__(self, studio: Window) -> None:
        self.studio = studio
        self.bar: Window | None = None
        self.hotkey: hotkeys.Registered | None = None
        self.lock = threading.Lock()
        self.left = 0
        self.top = 0

    def open(self, data: dict) -> dict:
        """Start recording `data["name"]` for the bot at `data["path"]`."""
        with self.lock:
            if self.bar is not None:
                return record_api.status()
            folder = Path(str(data.get("path", "")))
            screen = pill._screen_of(self.studio.handle())
            self.studio.hide()
            self.bar = open_window("recorder", "bar", extra={"width": BAR_WIDTH, "height": BAR_HEIGHT})
            self.bar.opened.wait(10)
            self.left = screen.left + (screen.right - screen.left - BAR_WIDTH) // 2
            self.top = screen.top
            pill._place(self.bar.handle(), self.left, self.top)
            record_api.ignore_area = self.area
            record_api.on_end = self.ended
            handlers = {"run.pause": record_api.pause, "record.toggle": self.stop_from_key}
            self.hotkey = hotkeys.register(_keys(), handlers)
            return record_api.start(folder, str(data.get("name", "")))

    def stop_from_key(self) -> None:
        record_api.stop(True)

    def area(self) -> tuple[int, int, int, int] | None:
        """Where the bar is on screen, so clicks on it aren't recorded."""
        if self.bar is None:
            return None
        width, height = pill._size_of(self.bar.handle())
        return (self.left, self.top, width, height)

    def size(self, data: dict) -> dict:
        """Make the bar taller for its menu or live steps, or back."""
        if self.bar is not None:
            height = PANEL_HEIGHT if data.get("open") else BAR_HEIGHT
            self.bar.native.resize(BAR_WIDTH, height)
        return {"ok": True}

    def ended(self, name: str | None) -> None:
        with self.lock:
            bar = self.bar
            self.bar = None
            if self.hotkey is not None:
                self.hotkey.stop()
                self.hotkey = None
        if bar is not None:
            bar.close()
        self.studio.show()
        if name:
            publish("studio.page", {"page": "action", "name": name})


def register(studio: Window) -> RecordWindow:
    from ..server.app import HANDLERS

    window = RecordWindow(studio)
    HANDLERS["record.start"] = window.open
    HANDLERS["record.size"] = window.size
    return window
