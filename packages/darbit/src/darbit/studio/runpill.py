"""The run pill (#130, #245): while a bot runs, darbit Studio hides and a small pill at the top of the screen shows
the bot, where it is, Pause, Stop and a way back to the Studio.

A few seconds after the mouse leaves it, the pill slides up and leaves a sliver at the top edge. A real mouse move
to that edge brings it back: the listener leaves out input a program sends, so the bot's own moves never show it.
RunPill.qml draws it; app.py opens it on Play and brings the Studio back when it closes.
"""

import threading
import time
from collections.abc import Callable
from dataclasses import dataclass

from PySide6.QtCore import Property, QObject, QTimer, Signal, Slot

HIDE_AFTER = 3.0  # seconds after the mouse leaves the pill before it slides away
EDGE = 2  # pixels from the top of the screen that bring it back
MARGIN = 24  # pixels around the pill that still count as on it
LOOK_MS = 250  # how often the pill checks whether it's time to slide away


@dataclass
class Peek:
    """Whether the pill shows, from where the real mouse is. The area is in screen pixels."""

    left: int = 0
    top: int = 0
    width: int = 0
    height: int = 0
    tucked: bool = False
    on_pill: bool = False
    left_at: float = 0.0

    def near(self, x: int) -> bool:
        return self.left - MARGIN <= x <= self.left + self.width + MARGIN

    def mouse(self, x: int, y: int, now: float) -> bool:
        """A real mouse move. True if the pill came back."""
        if self.tucked:
            if self.near(x) and y <= self.top + EDGE:
                self.tucked = False
                self.on_pill = True
                return True
            return False
        over = self.near(x) and y <= self.top + self.height + MARGIN
        if self.on_pill and not over:
            self.left_at = now
        self.on_pill = over
        return False

    def time_to_tuck(self, now: float) -> bool:
        return not self.tucked and not self.on_pill and now - self.left_at >= HIDE_AFTER


def _watch_mouse(on_move: Callable[[int, int], None]) -> Callable[[], None] | None:
    """Real mouse moves, or None on a system without the listener (the pill then never slides away)."""
    from ..platform import hooks
    from ..platform.backend import NotSupported

    try:
        return hooks.watch_mouse(on_move)
    except NotSupported:
        return None


class RunPill(QObject):
    changed = Signal()
    closed = Signal()  # the pill went away: app.py brings the Studio back
    _shown = Signal()  # from the listener's thread

    def __init__(self, watch: Callable[[Callable[[int, int], None]], Callable[[], None] | None] = _watch_mouse) -> None:
        super().__init__()
        self._watch = watch
        self._stop_watching: Callable[[], None] | None = None
        self._open = False
        self._peek = Peek()
        self._lock = threading.Lock()  # the peek is read on the listener's thread too
        self._timer = QTimer(self)
        self._timer.setInterval(LOOK_MS)
        self._timer.timeout.connect(self._look)
        self._shown.connect(self.changed)

    def _get_open(self) -> bool:
        return self._open

    def _get_tucked(self) -> bool:
        return self._peek.tucked

    isOpen = Property(bool, _get_open, notify=changed)
    tucked = Property(bool, _get_tucked, notify=changed)

    @Slot()
    def open(self) -> None:
        if self._open:
            return
        self._open = True
        with self._lock:
            self._peek.tucked = False
            self._peek.on_pill = False
            self._peek.left_at = time.monotonic()
        self._stop_watching = self._watch(self._moved)
        if self._stop_watching is not None:
            self._timer.start()
        self.changed.emit()

    @Slot()
    def close(self) -> None:
        if not self._open:
            return
        self._open = False
        self._timer.stop()
        if self._stop_watching is not None:
            self._stop_watching()
            self._stop_watching = None
        self.changed.emit()
        self.closed.emit()

    @Slot(int, int, int, int)
    def setArea(self, x: int, y: int, width: int, height: int) -> None:
        """Where the pill shows (not tucked), in screen pixels."""
        with self._lock:
            self._peek.left, self._peek.top, self._peek.width, self._peek.height = x, y, width, height

    def _moved(self, x: int, y: int) -> None:
        with self._lock:
            came_back = self._peek.mouse(x, y, time.monotonic())
        if came_back:
            self._shown.emit()

    def _look(self) -> None:
        with self._lock:
            tuck = self._peek.time_to_tuck(time.monotonic())
            if tuck:
                self._peek.tucked = True
        if tuck:
            self.changed.emit()
