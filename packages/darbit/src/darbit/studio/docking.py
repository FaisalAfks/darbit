"""Where a pill over the game sits (#384): docked on a screen edge at one of its snap places, or floating.

The maths works on plain rectangles in Qt's points, so it's tested without screens. `PillPlace` is the object each
pill's window drives while it's dragged; it keeps the pill's place in darbit's ui settings for next time.
"""

from collections.abc import Callable
from dataclasses import asdict, dataclass

from PySide6.QtCore import Property, QObject, QPointF, Signal, Slot

from ..server import ui_settings

EDGES = ("top", "bottom", "left", "right")
FLOATING = "float"
SNAPS = (0.0, 0.3, 0.5, 0.7, 1.0)  # along an edge: the corners, near the centre on each side, the centre
GAP = 8  # points between a docked pill and its edge
FLOAT_SHARE = 0.2  # past this share of the screen's smaller side from every edge, a dropped pill floats
FLOAT_LEAST = 150  # points: the float line is never closer to the edge than this
KEY = "studio.pill."  # ui setting per pill: studio.pill.run, studio.pill.capture, ...


@dataclass
class Rect:
    """A screen or a pill, in Qt's points."""

    x: float
    y: float
    width: float
    height: float

    @property
    def right(self) -> float:
        return self.x + self.width

    @property
    def bottom(self) -> float:
        return self.y + self.height


@dataclass
class Place:
    """Where a pill is: on `edge` at `along` (0 is the left or top corner, 1 the other), or floating with its centre
    at `x`, `y` (shares of the screen). The last edge it was docked on is kept, for Dock."""

    screen: str = ""
    edge: str = "top"
    along: float = 0.5
    x: float = 0.5
    y: float = 0.35
    docked_edge: str = "top"
    docked_along: float = 0.5

    @property
    def floating(self) -> bool:
        return self.edge == FLOATING


def free_edges(screen: Rect, others: list[Rect]) -> list[str]:
    """The screen's edges a pill can dock on: not one another screen touches, where tucking away would slide the pill
    onto that screen and the mouse could never stop at the edge to bring it back."""
    free = []
    for edge in EDGES:
        shared = False
        for other in others:
            if edge in ("top", "bottom"):
                meets = other.bottom == screen.y if edge == "top" else other.y == screen.bottom
                overlaps = other.x < screen.right and other.right > screen.x
            else:
                meets = other.right == screen.x if edge == "left" else other.x == screen.right
                overlaps = other.y < screen.bottom and other.bottom > screen.y
            if meets and overlaps:
                shared = True
        if not shared:
            free.append(edge)
    return free or ["top"]


def distance_to(screen: Rect, edge: str, x: float, y: float) -> float:
    if edge == "top":
        return y - screen.y
    if edge == "bottom":
        return screen.bottom - y
    if edge == "left":
        return x - screen.x
    return screen.right - x


def nearest_edge(screen: Rect, x: float, y: float, edges: list[str]) -> str:
    return min(edges, key=lambda edge: distance_to(screen, edge, x, y))


def float_line(screen: Rect) -> float:
    """How far from every edge a pill has to be dropped to float."""
    return max(FLOAT_LEAST, FLOAT_SHARE * min(screen.width, screen.height))


def floats(screen: Rect, x: float, y: float, edges: list[str]) -> bool:
    return distance_to(screen, nearest_edge(screen, x, y, edges), x, y) > float_line(screen)


def along_of(screen: Rect, edge: str, x: float, y: float) -> float:
    """Where a point is along an edge, from 0 to 1."""
    if edge in ("top", "bottom"):
        share = (x - screen.x) / max(1.0, screen.width)
    else:
        share = (y - screen.y) / max(1.0, screen.height)
    return min(1.0, max(0.0, share))


def snap(along: float) -> float:
    return min(SNAPS, key=lambda place: abs(place - along))


def spot(screen: Rect, edge: str, along: float, width: float, height: float) -> Rect:
    """Where a docked pill of this size sits: `along` 0 and 1 are flush in the corners."""
    if edge in ("top", "bottom"):
        x = screen.x + GAP + along * (screen.width - 2 * GAP - width)
        y = screen.y + GAP if edge == "top" else screen.bottom - GAP - height
    else:
        y = screen.y + GAP + along * (screen.height - 2 * GAP - height)
        x = screen.x + GAP if edge == "left" else screen.right - GAP - width
    return Rect(x, y, width, height)


def floating_spot(screen: Rect, x: float, y: float, width: float, height: float) -> Rect:
    """A floating pill with its centre at shares `x`, `y` of the screen, kept wholly on it."""
    left = screen.x + x * screen.width - width / 2
    top = screen.y + y * screen.height - height / 2
    left = min(max(left, screen.x + GAP), screen.right - GAP - width)
    top = min(max(top, screen.y + GAP), screen.bottom - GAP - height)
    return Rect(left, top, width, height)


def drop(place: Place, screen_name: str, screen: Rect, edges: list[str], x: float, y: float) -> Place:
    """The place a pill held at (x, y) goes to when it's let go: floating past the float line, else the nearest snap
    place of the nearest edge."""
    if floats(screen, x, y, edges):
        share_x = (x - screen.x) / max(1.0, screen.width)
        share_y = (y - screen.y) / max(1.0, screen.height)
        return Place(screen_name, FLOATING, place.along, share_x, share_y, place.docked_edge, place.docked_along)
    edge = nearest_edge(screen, x, y, edges)
    along = snap(along_of(screen, edge, x, y))
    return Place(screen_name, edge, along, place.x, place.y, edge, along)


def docked(place: Place) -> Place:
    """The floating pill back on the edge it was last docked on."""
    return Place(
        place.screen, place.docked_edge, place.docked_along, place.x, place.y, place.docked_edge, place.docked_along
    )


def read(saved: object, screens: dict[str, Rect], first: str) -> Place:
    """A kept place on the screens there are now: one on a screen that's gone (or an edge that's now shared) goes
    back to the top centre of the first screen."""
    if not isinstance(saved, dict):
        return Place(first)
    try:
        place = Place(
            str(saved.get("screen", "")),
            str(saved.get("edge", "top")),
            float(saved.get("along", 0.5)),
            float(saved.get("x", 0.5)),
            float(saved.get("y", 0.35)),
            str(saved.get("docked_edge", "top")),
            float(saved.get("docked_along", 0.5)),
        )
    except (TypeError, ValueError):
        return Place(first)
    if place.screen not in screens:
        return Place(first)
    edges = free_edges(screens[place.screen], [rect for name, rect in screens.items() if name != place.screen])
    if place.edge not in edges and not place.floating:
        return Place(place.screen)
    if place.docked_edge not in edges:
        place.docked_edge, place.docked_along = "top", 0.5
    place.along = snap(min(1.0, max(0.0, place.along)))
    place.x = min(1.0, max(0.0, place.x))
    place.y = min(1.0, max(0.0, place.y))
    return place


def form_of(edge: str) -> str:
    """The pill's form on an edge: a row on the top and bottom, a labelled column on the sides, a card floating."""
    if edge == FLOATING:
        return "card"
    if edge in ("left", "right"):
        return "column"
    return "row"


def qt_screens() -> dict[str, Rect]:
    """Every screen by name, in Qt's points (display scaling taken into account), the main one first."""
    from PySide6.QtGui import QGuiApplication

    found = {}
    primary = QGuiApplication.primaryScreen()
    ordered = [primary] + [screen for screen in QGuiApplication.screens() if screen is not primary]
    for screen in ordered:
        if screen is None:
            continue
        box = screen.geometry()
        found[screen.name()] = Rect(box.x(), box.y(), box.width(), box.height())
    return found or {"": Rect(0, 0, 1920, 1080)}


class PillPlace(QObject):
    """One pill's place, its form, and the feedback while it's dragged. The window asks `spotFor` where to sit."""

    changed = Signal()
    dragChanged = Signal()

    def __init__(
        self,
        name: str,
        screens: Callable[[], dict[str, Rect]] = qt_screens,
        keep: bool = True,
        in_window: bool = False,
    ) -> None:
        super().__init__()
        self._name = name
        self._screens = screens
        self._keep = keep
        self._in_window = in_window  # a pill inside one window (Capture's): that window is its only screen
        self._area = Rect(0, 0, 1920, 1080)
        self._near = "top"
        found = self._all()
        self._place = read(ui_settings.get(KEY + name) if keep else None, found, next(iter(found)))
        self._dragging = False
        self._preview = Place()
        self._preview_screen = Rect(0, 0, 0, 0)
        self._sizes = {"row": (480.0, 56.0), "column": (150.0, 220.0), "card": (420.0, 200.0)}
        self._follow_screens()

    def _follow_screens(self) -> None:
        """A screen plugged in or out, or its scaling changed: the pill finds its place again."""
        from PySide6.QtGui import QGuiApplication

        app = QGuiApplication.instance()
        if app is None or self._in_window:
            return
        app.screenAdded.connect(self._screens_changed)
        app.screenRemoved.connect(self._screens_changed)

    def _screens_changed(self, *screen: object) -> None:
        found = self._all()
        if self._place.screen not in found:
            self._place = read(None, found, next(iter(found)))
        self.changed.emit()

    def _all(self) -> dict[str, Rect]:
        if self._in_window:
            return {"": self._area}
        return self._screens()

    def _screen(self, name: str) -> Rect:
        found = self._all()
        return found.get(name, next(iter(found.values())))

    def _screen_at(self, x: float, y: float) -> str:
        found = self._all()
        for name, rect in found.items():
            if rect.x <= x < rect.right and rect.y <= y < rect.bottom:
                return name
        return next(iter(found))

    def _free(self, name: str) -> list[str]:
        found = self._all()
        return free_edges(found[name], [rect for other, rect in found.items() if other != name])

    def shown(self) -> Place:
        return self._preview if self._dragging else self._place

    def _get_edge(self) -> str:
        return self.shown().edge

    def _get_form(self) -> str:
        return form_of(self.shown().edge)

    def _get_floating(self) -> bool:
        return self.shown().floating

    def _get_dragging(self) -> bool:
        return self._dragging

    def _get_screen(self) -> dict:
        place = self.shown()
        return asdict(self._preview_screen if self._dragging else self._screen(place.screen))

    def _get_snaps(self) -> list:
        """While dragging: the snap places of the nearest edge (their centres), the one it'd go to marked."""
        if not self._dragging:
            return []
        screen = self._preview_screen
        edge = self._near
        width, height = self._sizes[form_of(edge)]
        spots = []
        for along in SNAPS:
            box = spot(screen, edge, along, width, height)
            spots.append(
                {
                    "x": box.x + box.width / 2,
                    "y": box.y + box.height / 2,
                    "on": not self._preview.floating and along == self._preview.along,
                }
            )
        return spots

    def _get_near(self) -> str:
        return self._near if self._dragging else ""

    def _get_line(self) -> float:
        return float_line(self._preview_screen) if self._dragging else 0.0

    edge = Property(str, _get_edge, notify=changed)
    form = Property(str, _get_form, notify=changed)
    floating = Property(bool, _get_floating, notify=changed)
    dragging = Property(bool, _get_dragging, notify=dragChanged)
    screen = Property("QVariantMap", _get_screen, notify=changed)
    snaps = Property(list, _get_snaps, notify=changed)
    near = Property(str, _get_near, notify=changed)
    line = Property(float, _get_line, notify=changed)

    @Slot(float, float, float, float)
    def useArea(self, x: float, y: float, width: float, height: float) -> None:
        """The size of the window a pill lives in (Capture's): its only screen, with every edge free."""
        if width <= 0 or height <= 0:
            return
        self._area = Rect(x, y, width, height)
        self.changed.emit()

    @Slot(str, float, float)
    def setSize(self, form: str, width: float, height: float) -> None:
        """The pill's size in a form, for the snap places shown while it's dragged."""
        self._sizes[form] = (width, height)

    @Slot(result="QPointF")
    def cursor(self) -> QPointF:
        """The mouse, in global points: read here, since the pill's window moves under it while it's dragged."""
        from PySide6.QtGui import QCursor

        return QPointF(QCursor.pos())

    @Slot(float, float)
    def begin(self, x: float, y: float) -> None:
        self._dragging = True
        self.dragChanged.emit()
        self.move(x, y)

    @Slot(float, float)
    def move(self, x: float, y: float) -> None:
        if not self._dragging:
            return
        name = self._screen_at(x, y)
        screen = self._screen(name)
        edges = self._free(name)
        self._preview_screen = screen
        self._near = nearest_edge(screen, x, y, edges)
        self._preview = drop(self._place, name, screen, edges, x, y)
        self.changed.emit()

    @Slot()
    def end(self) -> None:
        if not self._dragging:
            return
        self._place = self._preview
        self._dragging = False
        self._save()
        self.dragChanged.emit()
        self.changed.emit()

    @Slot()
    def cancel(self) -> None:
        if not self._dragging:
            return
        self._dragging = False
        self.dragChanged.emit()
        self.changed.emit()

    @Slot()
    def dock(self) -> None:
        """Back on the edge it was last docked on (the floating card's Dock)."""
        self._place = docked(self._place)
        self._save()
        self.changed.emit()

    @Slot(float, float, result="QVariantMap")
    def spotFor(self, width: float, height: float) -> dict:
        """Where the pill, this size in its form now, sits: {x, y} in Qt's points."""
        place = self.shown()
        screen = self._preview_screen if self._dragging else self._screen(place.screen)
        if place.floating:
            box = floating_spot(screen, place.x, place.y, width, height)
        else:
            box = spot(screen, place.edge, place.along, width, height)
        return {"x": box.x, "y": box.y}

    def _save(self) -> None:
        if self._keep:
            ui_settings.set_value(KEY + self._name, asdict(self._place))
