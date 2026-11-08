"""A floating pill that hides over the game (#245): the run pill while a bot runs, Scout's and the recorder's.

Open, it shows; a few seconds after the real mouse leaves it, it slides out of sight past the screen edge it's docked
on (#384). A real mouse move to that edge beside it brings it back: the listener leaves out input a program sends, so
a bot's own moves never show it. A floating pill, or one being dragged, never hides. PillWindow.qml places the pills;
app.py opens and closes them.
"""

import threading
import time
from collections.abc import Callable
from dataclasses import dataclass

from PySide6.QtCore import Property, QObject, QTimer, Signal, Slot

from .docking import Rect

HIDE_AFTER = 3.0  # seconds after the mouse leaves the pill before it slides away
EDGE = 2  # pixels from the top of the screen that bring it back
MARGIN = 24  # pixels around the pill that still count as on it
LOOK_MS = 250  # how often the pill checks whether it's time to slide away


@dataclass
class Peek:
    """Whether the pill shows, from where the real mouse is. The area is in screen pixels: the pill where it shows,
    stretched to the screen edge it's docked on (`edge`), so that side of the area is the screen's edge."""

    left: int = 0
    top: int = 0
    width: int = 0
    height: int = 0
    edge: str = "top"
    tucked: bool = False
    on_pill: bool = False
    left_at: float = 0.0
    held: bool = False  # floating or being dragged: it stays

    def beside(self, x: int, y: int) -> bool:
        """Along the edge, level with the pill."""
        if self.edge in ("top", "bottom"):
            return self.left - MARGIN <= x <= self.left + self.width + MARGIN
        return self.top - MARGIN <= y <= self.top + self.height + MARGIN

    def at_edge(self, x: int, y: int) -> bool:
        if self.edge == "bottom":
            return y >= self.top + self.height - 1 - EDGE
        if self.edge == "left":
            return x <= self.left + EDGE
        if self.edge == "right":
            return x >= self.left + self.width - 1 - EDGE
        return y <= self.top + EDGE

    def over(self, x: int, y: int) -> bool:
        inside_x = self.left - MARGIN <= x <= self.left + self.width + MARGIN
        inside_y = self.top - MARGIN <= y <= self.top + self.height + MARGIN
        return inside_x and inside_y

    def mouse(self, x: int, y: int, now: float) -> bool:
        """A real mouse move. True if the pill came back."""
        if self.tucked:
            if self.beside(x, y) and self.at_edge(x, y):
                self.tucked = False
                self.on_pill = True
                return True
            return False
        over = self.over(x, y)
        if self.on_pill and not over:
            self.left_at = now
        self.on_pill = over
        return False

    def time_to_tuck(self, now: float) -> bool:
        if self.held:
            return False
        return not self.tucked and not self.on_pill and now - self.left_at >= HIDE_AFTER


def to_pixels(box: Rect, screen: Rect, ratio: float) -> Rect:
    """A box in Qt's points on a screen, in screen pixels. Qt keeps each screen's top-left corner where it is in
    pixels and scales from there, so with display scaling the screen's origin matters, not only the ratio."""
    return Rect(
        round(screen.x + (box.x - screen.x) * ratio),
        round(screen.y + (box.y - screen.y) * ratio),
        round(box.width * ratio),
        round(box.height * ratio),
    )


def screen_of(x: float, y: float) -> tuple[Rect, float]:
    """The screen a point (Qt's points) is on, and its display scaling."""
    from PySide6.QtCore import QPoint
    from PySide6.QtGui import QGuiApplication

    screen = QGuiApplication.screenAt(QPoint(round(x), round(y))) or QGuiApplication.primaryScreen()
    if screen is None:
        return Rect(0, 0, 0, 0), 1.0
    geometry = screen.geometry()
    return Rect(geometry.x(), geometry.y(), geometry.width(), geometry.height()), screen.devicePixelRatio()


def _watch_mouse(on_move: Callable[[int, int], None]) -> Callable[[], None] | None:
    """Real mouse moves, or None on a system without the listener (the pill then never slides away)."""
    from ..platform import hooks
    from ..platform.backend import NotSupported

    try:
        return hooks.watch_mouse(on_move)
    except NotSupported:
        return None


def told_by_window(on_move: Callable[[int, int], None]) -> Callable[[], None]:
    """No listener: the pill's own window tells it where the mouse is (`moveTo`), as Capture's full-screen one does."""
    return lambda: None


class HidingPill(QObject):
    changed = Signal()
    closed = Signal()  # the pill went away (the run pill's: app.py brings the Studio back)
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
        """Where the pill shows (not tucked) stretched to its edge, in screen pixels."""
        with self._lock:
            self._peek.left, self._peek.top, self._peek.width, self._peek.height = x, y, width, height

    @Slot(float, float, float, float, str)
    def setShown(self, x: float, y: float, width: float, height: float, edge: str) -> None:
        """Where the pill shows stretched to the edge it's docked on, in Qt's points; "float" when it floats."""
        screen, ratio = screen_of(x + width / 2, y + height / 2)
        box = to_pixels(Rect(x, y, width, height), screen, ratio)
        with self._lock:
            self._peek.edge = edge if edge != "float" else "top"
        self.setArea(int(box.x), int(box.y), int(box.width), int(box.height))

    @Slot(int, int, int, int, str)
    def setPlace(self, x: int, y: int, width: int, height: int, edge: str) -> None:
        """For a pill inside one window (Capture's): its area stretched to its edge, in that window's points, which
        `moveTo` is told the mouse in."""
        with self._lock:
            self._peek.edge = edge if edge != "float" else "top"
        self.setArea(x, y, width, height)

    @Slot(int, int)
    def moveTo(self, x: int, y: int) -> None:
        """The mouse moved, from a pill's own window rather than the listener (Capture's, which sees every move)."""
        self._moved(x, y)

    @Slot()
    def show(self) -> None:
        """Back in sight now, and hidden again a few seconds after the mouse leaves it (a message to read)."""
        with self._lock:
            was_tucked = self._peek.tucked
            self._peek.tucked = False
            self._peek.left_at = time.monotonic()
        if was_tucked:
            self.changed.emit()

    @Slot(bool)
    def hold(self, held: bool) -> None:
        """A floating pill, or one being dragged, stays shown."""
        with self._lock:
            self._peek.held = held
            self._peek.left_at = time.monotonic()  # let go: it waits the usual time before hiding
            came_back = held and self._peek.tucked
            if came_back:
                self._peek.tucked = False
        if came_back:
            self.changed.emit()

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
