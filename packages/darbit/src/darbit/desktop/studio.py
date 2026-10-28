"""darbit Studio's own window: it opens where it was left, and closing it keeps darbit running in the tray.

`darbit app` calls `open_studio()`. The window's place and size are saved in the UI settings as it moves and
opens there again if that spot is still on a screen. Closing hides it instead of quitting (unless the
"Closing the window" setting says Quit); a running bot then keeps its run pill. See decision 0013.
"""

import threading
import time

from ..platform import windows
from ..server import hub, ui_settings
from . import capture_window, pill, record_window, tray
from .windows import Window, open_window

PLACE = "studio.window"  # ui setting: {"x", "y", "width", "height"} the Studio was last left at
CLOSING = "studio.closing"  # ui setting: "tray" (keep running, the default) or "quit"
MIN_SIZE = (900, 600)
BACKGROUND = "#0b0d12"  # shown before the page draws, so the window never flashes white
SAVE_AFTER = 0.5  # seconds of no moving before the place is saved
OFF_SCREEN = -10000  # Windows parks minimised windows at -32000
GIVE_BACK_FOCUS = 0.3  # seconds for Windows to hand the keyboard back to the game after the Studio hides


def saved_place(saved: object, screens: list[tuple[int, int, int, int]]) -> dict | None:
    """The saved place and size, if its title bar is still on one of the screens (x, y, width, height)."""
    if not isinstance(saved, dict):
        return None
    try:
        x = int(saved["x"])
        y = int(saved["y"])
        width = int(saved["width"])
        height = int(saved["height"])
    except (KeyError, TypeError, ValueError):
        return None
    if width < MIN_SIZE[0] or height < MIN_SIZE[1]:
        return None
    grab_x = x + 60  # a point on the title bar that must be reachable to drag the window back
    grab_y = y + 15
    for left, top, screen_width, screen_height in screens:
        if left <= grab_x < left + screen_width and top <= grab_y < top + screen_height:
            return {"x": x, "y": y, "width": width, "height": height}
    return None


def _screens() -> list[tuple[int, int, int, int]]:
    import webview

    found = []
    for screen in webview.screens:  # a list behind a lazy proxy, filled on first use
        found.append((screen.x, screen.y, screen.width, screen.height))
    return found


class Place:
    """Keeps the window's place up to date and saves it once it stops moving."""

    def __init__(self, start: dict) -> None:
        self.values = dict(start)
        self.timer: threading.Timer | None = None

    def moved(self, x: int, y: int) -> None:
        if x < OFF_SCREEN or y < OFF_SCREEN:
            return  # minimised
        self.values["x"] = x
        self.values["y"] = y
        self.save_soon()

    def resized(self, width: int, height: int) -> None:
        if width < MIN_SIZE[0] or height < MIN_SIZE[1]:
            return  # minimised or squeezed by Windows
        self.values["width"] = width
        self.values["height"] = height
        self.save_soon()

    def save_soon(self) -> None:
        if self.timer is not None:
            self.timer.cancel()
        self.timer = threading.Timer(SAVE_AFTER, self.save)
        self.timer.daemon = True
        self.timer.start()

    def save(self) -> None:
        if "x" in self.values:
            ui_settings.set_value(PLACE, self.values)


def open_studio() -> Window:
    """Open the Studio where it was left, with the tray icon and the run pill."""
    extra = {"background_color": BACKGROUND, "min_size": MIN_SIZE}
    place = saved_place(ui_settings.get(PLACE), _screens())
    if place is not None:
        extra.update(place)
    studio = open_window("hub", extra=extra)
    remember = Place(place or {})
    studio.native.events.moved += remember.moved
    studio.native.events.resized += remember.resized
    run_pill = pill.register(studio)
    capture_window.register(studio)
    record_window.register(studio)
    icon = tray.Tray(studio, run_pill)
    quitting = threading.Event()

    def closing() -> bool:
        """Hide to the tray instead of quitting, unless the setting says Quit."""
        remember.save()
        if quitting.is_set():
            return True
        if ui_settings.get(CLOSING, "tray") == "quit":
            quitting.set()
            threading.Thread(target=icon.quit, name="darbit-quit", daemon=True).start()
            return False
        threading.Thread(target=hide, name="darbit-hide", daemon=True).start()
        return False  # keep the window, just hidden

    def hide() -> None:
        running = hub.running()
        if running:
            run_pill.collapse({"path": str(running[0])})
        else:
            studio.hide()

    from ..server.app import HANDLERS

    studio.native.events.closing += closing
    icon.on_quit = quitting.set

    def show(data: dict) -> None:
        icon.show_studio()
        if not run_pill.collapsed.is_set():
            windows.bring_to_front(studio.handle())  # shown isn't enough: it must come in front of the game

    HANDLERS["studio.show"] = show  # a second `darbit app` brings this one forward
    studio.native.events.shown += icon.start
    hide_while_playing(studio)
    return studio


def hide_while_playing(studio: Window) -> None:
    """Playing an action hides the Studio, so its clicks and keys reach the game; it comes back when the
    action stops at a breakpoint or ends."""
    from .. import events
    from ..server.app import HANDLERS

    play = HANDLERS.get("actions.play")
    control = HANDLERS.get("actions.control")
    if play is None or control is None:
        return  # the server runs in another process, which plays its actions itself

    def get_out_of_the_way() -> None:
        studio.hide()
        time.sleep(GIVE_BACK_FOCUS)

    def play_hidden(data: dict) -> object:
        get_out_of_the_way()
        try:
            return play(data)
        except Exception:
            studio.show()
            raise

    def control_hidden(data: dict) -> object:
        if data.get("what") in ("resume", "step"):
            get_out_of_the_way()
        return control(data)

    def on_event(topic: str, data: dict) -> None:
        if topic in ("action.paused", "action.ended"):
            studio.show()

    HANDLERS["actions.play"] = play_hidden
    HANDLERS["actions.control"] = control_hidden
    events.listen(on_event)
