"""The run pill: while a bot runs, darbit Studio collapses into a small bar at the top of the screen (#130).

The bar slides up out of sight a few seconds after the mouse leaves it, leaving a sliver at the top edge.
Moving the mouse to that edge brings it back, but only a real move: darbit's own input is injected and the
mouse hook skips it, so a running bot never shows the bar. Expand, or the bot ending, brings the Studio back.
"""

import ctypes
import threading
import time
from ctypes import wintypes
from dataclasses import dataclass

from .. import events
from ..server import ui_settings
from .windows import Window, open_window

HIDE_AFTER = 3.0  # seconds after the mouse leaves the bar (the studio.pill_hide_after setting; 0 never hides)
EDGE = 2  # pixels from the top of the screen that bring it back
PEEK = 4  # pixels of the bar left showing when it's hidden
MARGIN = 24  # pixels around the bar that still count as on it
SLIDE_STEPS = 6  # moves in a slide, about 120 ms in all
TICK = 0.1  # seconds between looks at the mouse state


@dataclass
class Peek:
    """Whether the bar should show, from where the mouse is (no windows: tested on its own)."""

    left: int
    top: int  # the screen's top edge, where the shown bar sits
    width: int
    height: int
    shown: bool = True
    on_bar: bool = False
    left_bar_at: float = 0.0
    hide_after: float = HIDE_AFTER

    def near(self, x: int) -> bool:
        return self.left - MARGIN <= x <= self.left + self.width + MARGIN

    def mouse(self, x: int, y: int, now: float) -> None:
        """A real mouse move."""
        if not self.shown:
            if self.near(x) and y <= self.top + EDGE:
                self.shown = True
                self.on_bar = True
            return
        over = self.near(x) and y <= self.top + self.height + MARGIN
        if self.on_bar and not over:
            self.left_bar_at = now
        self.on_bar = over

    def should_hide(self, now: float) -> bool:
        if self.hide_after <= 0:
            return False
        return self.shown and not self.on_bar and now - self.left_bar_at >= self.hide_after

    def hidden_top(self) -> int:
        return self.top - self.height + PEEK


def hide_after() -> float:
    """Seconds the bar waits before sliding away, from the Studio settings."""
    value = ui_settings.get("studio.pill_hide_after", HIDE_AFTER)
    if isinstance(value, (int, float)) and value >= 0:
        return float(value)
    return HIDE_AFTER


class RECT(ctypes.Structure):
    _fields_ = [("left", ctypes.c_long), ("top", ctypes.c_long), ("right", ctypes.c_long), ("bottom", ctypes.c_long)]


class MONITORINFO(ctypes.Structure):
    _fields_ = [("cbSize", wintypes.DWORD), ("rcMonitor", RECT), ("rcWork", RECT), ("dwFlags", wintypes.DWORD)]


HWND_TOPMOST = -1
SWP_NOSIZE = 0x0001
SWP_NOACTIVATE = 0x0010
MONITOR_DEFAULTTONEAREST = 2


def _screen_of(handle: int) -> RECT:
    """The monitor a window is on, in screen pixels."""
    user32 = ctypes.windll.user32
    monitor = user32.MonitorFromWindow(ctypes.c_void_p(handle), MONITOR_DEFAULTTONEAREST)
    info = MONITORINFO()
    info.cbSize = ctypes.sizeof(MONITORINFO)
    user32.GetMonitorInfoW(ctypes.c_void_p(monitor), ctypes.byref(info))
    return info.rcMonitor


def _size_of(handle: int) -> tuple[int, int]:
    rect = RECT()
    ctypes.windll.user32.GetWindowRect(ctypes.c_void_p(handle), ctypes.byref(rect))
    return rect.right - rect.left, rect.bottom - rect.top


def _place(handle: int, x: int, y: int) -> None:
    flags = SWP_NOSIZE | SWP_NOACTIVATE
    ctypes.windll.user32.SetWindowPos(ctypes.c_void_p(handle), ctypes.c_void_p(HWND_TOPMOST), x, y, 0, 0, flags)


class RunPill:
    """Collapses the Studio window into the bar and back."""

    def __init__(self, main: Window) -> None:
        self.main = main
        self.bar: Window | None = None
        self.path = ""
        self.peek: Peek | None = None
        self.at_top = 0  # where the bar is now
        self.lock = threading.Lock()
        self.stop_hook = None
        self.collapsed = threading.Event()
        events.listen(self.on_event)

    def collapse(self, data: dict) -> dict:
        """Hide the Studio and show the bar for the bot at data["path"]."""
        from ..platform import hooks

        if self.collapsed.is_set():
            return {"collapsed": True}
        self.path = str(data.get("path", ""))
        screen = _screen_of(self.main.handle())
        self.bar = open_window("hub", "bar", query={"view": "pill", "path": self.path})
        if not self.bar.opened.wait(10):
            raise RuntimeError("the run pill's window didn't open")
        width, height = _size_of(self.bar.handle())
        left = screen.left + (screen.right - screen.left - width) // 2
        with self.lock:
            self.peek = Peek(left, screen.top, width, height, left_bar_at=time.monotonic(), hide_after=hide_after())
        self.at_top = screen.top
        _place(self.bar.handle(), left, screen.top)
        self.main.hide()
        self.collapsed.set()
        self.stop_hook = hooks.watch_mouse(self.on_mouse)
        threading.Thread(target=self.follow, name="darbit-run-pill", daemon=True).start()
        return {"collapsed": True}

    def expand(self, data: dict) -> dict:
        """Bring the Studio back and put the bar away."""
        if not self.collapsed.is_set():
            return {"collapsed": False}
        self.collapsed.clear()
        if self.stop_hook is not None:
            self.stop_hook()
            self.stop_hook = None
        self.main.show()
        if self.bar is not None:
            self.bar.close()
            self.bar = None
        return {"collapsed": False}

    def on_mouse(self, x: int, y: int) -> None:
        with self.lock:
            if self.peek is not None:
                self.peek.mouse(x, y, time.monotonic())

    def on_event(self, topic: str, data: dict) -> None:
        if topic != "project.status" or data.get("path") != self.path:
            return
        if data.get("status") in ("stopped", "failed") and self.collapsed.is_set():
            self.expand({})

    def follow(self) -> None:
        """Slide the bar in or out as Peek says, until the Studio expands."""
        while self.collapsed.is_set():
            with self.lock:
                peek = self.peek
                if peek is not None and peek.should_hide(time.monotonic()):
                    peek.shown = False
            bar = self.bar
            if peek is not None and bar is not None:
                wanted = peek.top if peek.shown else peek.hidden_top()
                if wanted != self.at_top:
                    self.slide(bar, peek.left, wanted)
            time.sleep(TICK)

    def slide(self, bar: Window, left: int, wanted: int) -> None:
        start = self.at_top
        for step in range(1, SLIDE_STEPS + 1):
            top = start + (wanted - start) * step // SLIDE_STEPS
            _place(bar.handle(), left, top)
            time.sleep(0.02)
        self.at_top = wanted


def register(main: Window) -> RunPill:
    """Add studio.collapse and studio.expand to the server, for the Studio window `main`."""
    from ..server.app import HANDLERS

    pill = RunPill(main)
    HANDLERS["studio.collapse"] = pill.collapse
    HANDLERS["studio.expand"] = pill.expand
    return pill
