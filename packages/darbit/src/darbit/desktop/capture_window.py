"""Opening the web capture tool from darbit Studio: hide the Studio, freeze the screen, show the overlay.

The screen is frozen before the overlay appears, so the overlay never photographs itself. With a setup guide,
saving one picture hides the overlay and shows a small bar naming the next one: open that screen in the game,
then press Ctrl+Alt+C (the keymap's capture.freeze) or the bar's button to freeze again. Closing brings the
Studio back. Decision 0013, round 7.
"""

import threading
import time
from pathlib import Path

from .. import keymap
from ..capture import service
from ..capture.common import Item
from ..platform import hotkeys
from ..project.manifest import load
from ..server import capture_api
from ..server.events import publish
from .windows import Window, open_window

HIDE_WAIT = 0.35  # seconds for darbit's windows to disappear before the screen is grabbed


def items_for(folder: Path, mode: str, name: str, kind: str) -> list[Item]:
    """What to take: the guide's pictures not taken yet, one named asset, or nothing set (anything)."""
    if mode == "one" and name:
        capture_kind = "location" if kind == "point" else kind
        return [Item(name, capture_kind or "image")]
    if mode != "guide":
        return []
    guide_file = folder / "guide.toml"
    if not guide_file.is_file():
        return []
    from ..capture.guide import load as load_guide
    from ..capture.guide import steps

    found = []
    for step in steps(load_guide(guide_file)):
        found.append(Item(step.name, step.kind, step.take.say or step.screen.say, step.screen.name))
    return found


def _freeze_key() -> str:
    try:
        return keymap.defaults()["global"].get("capture.freeze", "ctrl+alt+c")
    except (KeyError, OSError, ValueError):
        return "ctrl+alt+c"


class CaptureWindow:
    """The capture overlay, and the bar between guide items, for one Studio window."""

    def __init__(self, studio: Window) -> None:
        self.studio = studio
        self.window: Window | None = None
        self.bar: Window | None = None
        self.hotkey: hotkeys.Registered | None = None
        self.lock = threading.Lock()

    def open(self, data: dict) -> dict:
        """Start capturing for a bot: data has its path, the mode (guide, one, new) and an asset's name."""
        with self.lock:
            if self.window is not None:
                return {"open": True}
            folder = Path(str(data.get("path", "")))
            project = load(folder)
            images = folder / (project.images[0] if project.images else "images")
            images.mkdir(parents=True, exist_ok=True)
            mode = str(data.get("mode", "new"))
            items = items_for(folder, mode, str(data.get("name", "")), str(data.get("kind", "image")))
            test = str(data.get("name", "")) if mode == "test" else None
            started = service.start(folder, images, items, test)
            if mode == "guide" and not started["items"]:
                return {"open": False, "items": []}  # every picture is already taken
            self.studio.hide()
            time.sleep(HIDE_WAIT)
            service.freeze()
            self.window = open_window("capture", "overlay")
            capture_api.on_close = self.closed
            capture_api.on_next = self.between
            capture_api.on_refreeze = self.refreeze
            self.hotkey = hotkeys.register({"capture.freeze": _freeze_key()}, {"capture.freeze": self.refreeze})
            return {"open": True, "items": started["items"]}

    def between(self) -> None:
        """After a save with more to take: hide the overlay and show the bar naming the next picture."""
        if self.window is not None:
            self.window.hide()
        if self.bar is None:
            self.bar = open_window("capture", "bar", query={"view": "next"})
        else:
            self.bar.show()
            publish("capture.waiting", {})

    def refreeze(self) -> None:
        """Freeze the screen again: hide darbit's windows, grab, then show the overlay with the new shot."""
        if self.window is None:
            return
        if self.bar is not None:
            self.bar.hide()
        self.window.hide()
        time.sleep(HIDE_WAIT)
        service.freeze()
        self.window.show()
        publish("capture.frozen", {})

    def closed(self) -> None:
        with self.lock:
            window = self.window
            bar = self.bar
            self.window = None
            self.bar = None
            if self.hotkey is not None:
                self.hotkey.stop()
                self.hotkey = None
        if bar is not None:
            bar.close()
        if window is not None:
            window.close()
        self.studio.show()


def register(studio: Window) -> CaptureWindow:
    from ..server.app import HANDLERS

    capture = CaptureWindow(studio)
    HANDLERS["capture.open"] = capture.open
    return capture
