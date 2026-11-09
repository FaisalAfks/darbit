"""Where a pill over the game sits (#384, #449): docked on a screen edge where it was dropped, or floating.

Pills sit in each screen's work area (the screen less its taskbar) and stay where they're dropped, pulled onto an
edge's centre or a corner only when dropped very close to one. The maths works on plain rectangles in Qt's points, so
it's tested without screens. `PillPlace` is the object each pill's window drives while it's dragged; it keeps the
pill's place in darbit's ui settings for next time.
"""

from collections.abc import Callable
from dataclasses import asdict, dataclass

from PySide6.QtCore import Property, QObject, QPointF, Signal, Slot

from ..platform.system import HiddenTaskbar
from ..server import ui_settings

EDGES = ("top", "bottom", "left", "right")
FLOATING = "float"
SPOTS = (0.0, 0.5, 1.0)  # along an edge: the corners and the centre, which a drop very close to is pulled onto
PULL = 24  # points along the edge: a drop this close to a spot lands on it
GAP = 8  # points between a docked pill and its edge
FLOAT_SHARE = 0.2  # past this share of the screen's smaller side from every edge, a dropped pill floats
FLOAT_LEAST = 150  # points: the float line is never closer to the edge than this
TOUCH = 2  # pixels: screens this close meet
KEY = "studio.pill."  # ui setting per pill: studio.pill.run, studio.pill.capture, ...
SIZES = {"row": (480.0, 56.0), "column": (150.0, 220.0), "card": (420.0, 200.0)}  # until the pill says its own


@dataclass
class Rect:
    """A screen or a pill, in Qt's points. A screen's `ratio` is its display scaling (1.5 at 150%), and `work` its
    work area: the screen less its taskbar, where pills sit (None: all of it)."""

    x: float
    y: float
    width: float
    height: float
    ratio: float = 1.0
    work: "Rect | None" = None

    @property
    def right(self) -> float:
        return self.x + self.width

    @property
    def bottom(self) -> float:
        return self.y + self.height


@dataclass
class Held:
    """A pill being dragged: the mouse at `x`, `y`, holding the pill at shares `grab_x`, `grab_y` of its size, and the
    pill's size in each form (row, column, card)."""

    x: float
    y: float
    grab_x: float = 0.5
    grab_y: float = 0.5
    sizes: dict[str, tuple[float, float]] | None = None

    def size(self, form: str) -> tuple[float, float]:
        sizes = self.sizes or SIZES
        return sizes.get(form, SIZES[form])

    def top_left(self, form: str) -> tuple[float, float]:
        """Where the pill's top-left corner is in this form, the mouse holding it at the same shares."""
        width, height = self.size(form)
        return self.x - self.grab_x * width, self.y - self.grab_y * height


@dataclass
class Place:
    """Where a pill is: on `edge` at `along` (0 is the left or top corner, 1 the other), or floating with its centre
    at `x`, `y` (shares of the work area). The last edge it was docked on is kept, for Dock."""

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


def work_of(screen: Rect) -> Rect:
    """Where pills sit on a screen: its work area, or all of it."""
    if screen.work is None:
        return screen
    return screen.work


def less_taskbars(screen: Rect, work: Rect, bars: list[HiddenTaskbar]) -> Rect:
    """The work area less room for taskbars that hide themselves: Windows counts their edge as free, but the bar
    slides out over a pill there. An edge the work area already stops short of is left as it is."""
    left, top, right, bottom = work.x, work.y, work.right, work.bottom
    for bar in bars:
        room = bar.size / screen.ratio
        if bar.edge == "top" and touches(top, screen.y):
            top = screen.y + room
        elif bar.edge == "bottom" and touches(bottom, screen.bottom):
            bottom = screen.bottom - room
        elif bar.edge == "left" and touches(left, screen.x):
            left = screen.x + room
        elif bar.edge == "right" and touches(right, screen.right):
            right = screen.right - room
    return Rect(left, top, max(1.0, right - left), max(1.0, bottom - top))


def in_pixels(screen: Rect) -> Rect:
    """A screen as the system lays it out, in pixels. Qt keeps each screen's top-left corner where it is in pixels and
    scales its size, so with different scaling screens that touch don't touch in Qt's points."""
    return Rect(screen.x, screen.y, screen.width * screen.ratio, screen.height * screen.ratio)


def touches(a: float, b: float) -> bool:
    return abs(a - b) <= TOUCH


def free_edges(screen: Rect, others: list[Rect]) -> list[str]:
    """The screen's edges a pill can dock on: not one another screen touches, where tucking away would slide the pill
    onto that screen and the mouse could never stop at the edge to bring it back."""
    mine = in_pixels(screen)
    free = []
    for edge in EDGES:
        shared = False
        for other_screen in others:
            other = in_pixels(other_screen)
            if edge in ("top", "bottom"):
                meets = touches(other.bottom, mine.y) if edge == "top" else touches(other.y, mine.bottom)
                overlaps = other.x < mine.right and other.right > mine.x
            else:
                meets = touches(other.right, mine.x) if edge == "left" else touches(other.x, mine.right)
                overlaps = other.y < mine.bottom and other.bottom > mine.y
            if meets and overlaps:
                shared = True
        if not shared:
            free.append(edge)
    return free or ["top"]


def distance_to(area: Rect, edge: str, x: float, y: float) -> float:
    if edge == "top":
        return y - area.y
    if edge == "bottom":
        return area.bottom - y
    if edge == "left":
        return x - area.x
    return area.right - x


def nearest_edge(area: Rect, x: float, y: float, edges: list[str]) -> str:
    return min(edges, key=lambda edge: distance_to(area, edge, x, y))


def float_line(area: Rect) -> float:
    """How far from every edge a pill has to be dropped to float."""
    return max(FLOAT_LEAST, FLOAT_SHARE * min(area.width, area.height))


def floats(area: Rect, x: float, y: float, edges: list[str]) -> bool:
    return distance_to(area, nearest_edge(area, x, y, edges), x, y) > float_line(area)


def track(area: Rect, edge: str, width: float, height: float) -> float:
    """How far a docked pill of this size can move along an edge, in points, from one corner to the other."""
    if edge in ("top", "bottom"):
        return max(0.0, area.width - 2 * GAP - width)
    return max(0.0, area.height - 2 * GAP - height)


def along_of(area: Rect, edge: str, left: float, top: float, width: float, height: float) -> float:
    """Where a pill with its top-left corner at `left`, `top` is along an edge, from 0 to 1: `spot` the other way
    round, so a pill dropped there stays there."""
    room = track(area, edge, width, height)
    if room <= 0:
        return 0.5
    if edge in ("top", "bottom"):
        share = (left - area.x - GAP) / room
    else:
        share = (top - area.y - GAP) / room
    return min(1.0, max(0.0, share))


def pull(along: float, room: float) -> float:
    """A place along an edge, pulled onto a corner or the centre when it's within PULL points of one."""
    nearest = min(SPOTS, key=lambda place: abs(place - along))
    if abs(nearest - along) * room <= PULL:
        return nearest
    return along


def spot(area: Rect, edge: str, along: float, width: float, height: float) -> Rect:
    """Where a docked pill of this size sits in a work area: `along` 0 and 1 are flush in the corners."""
    if edge in ("top", "bottom"):
        x = area.x + GAP + along * track(area, edge, width, height)
        y = area.y + GAP if edge == "top" else area.bottom - GAP - height
    else:
        y = area.y + GAP + along * track(area, edge, width, height)
        x = area.x + GAP if edge == "left" else area.right - GAP - width
    return Rect(x, y, width, height)


def floating_spot(area: Rect, x: float, y: float, width: float, height: float) -> Rect:
    """A floating pill with its centre at shares `x`, `y` of the work area, kept wholly inside it."""
    left = area.x + x * area.width - width / 2
    top = area.y + y * area.height - height / 2
    left = max(area.x + GAP, min(left, area.right - GAP - width))
    top = max(area.y + GAP, min(top, area.bottom - GAP - height))
    return Rect(left, top, width, height)


def drop(place: Place, screen_name: str, screen: Rect, edges: list[str], held: Held) -> Place:
    """The place a held pill goes to when it's let go: floating where it is past the float line, else on the nearest
    edge where it is along it (pulled onto a corner or the centre only when very close to one)."""
    area = work_of(screen)
    if floats(area, held.x, held.y, edges):
        width, height = held.size("card")
        left, top = held.top_left("card")
        share_x = (left + width / 2 - area.x) / max(1.0, area.width)
        share_y = (top + height / 2 - area.y) / max(1.0, area.height)
        return Place(screen_name, FLOATING, place.along, share_x, share_y, place.docked_edge, place.docked_along)
    edge = nearest_edge(area, held.x, held.y, edges)
    width, height = held.size(form_of(edge))
    left, top = held.top_left(form_of(edge))
    along = pull(along_of(area, edge, left, top, width, height), track(area, edge, width, height))
    return Place(screen_name, edge, along, place.x, place.y, edge, along)


def docked(place: Place) -> Place:
    """The floating pill back on the edge it was last docked on."""
    return Place(
        place.screen, place.docked_edge, place.docked_along, place.x, place.y, place.docked_edge, place.docked_along
    )


def read(saved: object, screens: dict[str, Rect], first: str) -> Place:
    """A kept place on the screens there are now: one on a screen that's gone (or an edge that's now shared) goes
    back to the top centre of the first screen. Places are shares of the work area, so the pill stays inside it when
    the taskbar or the screen changes size."""
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
    place.along = min(1.0, max(0.0, place.along))
    place.docked_along = min(1.0, max(0.0, place.docked_along))
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


def box_of(rect: Rect) -> dict:
    """A rectangle for QML: {x, y, width, height}."""
    return {"x": rect.x, "y": rect.y, "width": rect.width, "height": rect.height}


def qt_screens() -> dict[str, Rect]:
    """Every screen by name, in Qt's points (display scaling taken into account), with its work area, the main one
    first."""
    from PySide6.QtGui import QGuiApplication

    from ..platform import system

    found = {}
    primary = QGuiApplication.primaryScreen()
    ordered = [primary] + [screen for screen in QGuiApplication.screens() if screen is not primary]
    for screen in ordered:
        if screen is None:
            continue
        box = screen.geometry()
        ratio = screen.devicePixelRatio()
        rect = Rect(box.x(), box.y(), box.width(), box.height(), ratio)
        free = screen.availableGeometry()
        pixels = in_pixels(rect)
        bars = system.hidden_taskbars(round(pixels.x), round(pixels.y), round(pixels.right), round(pixels.bottom))
        rect.work = less_taskbars(rect, Rect(free.x(), free.y(), free.width(), free.height()), bars)
        found[screen.name()] = rect
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
        self._found: dict[str, Rect] | None = None  # the screens, read again when they change and at each drag
        found = self._all()
        self._place = read(ui_settings.get(KEY + name) if keep else None, found, next(iter(found)))
        self._dragging = False
        self._preview = Place()
        self._preview_screen = Rect(0, 0, 0, 0)
        self._sizes = dict(SIZES)
        self._grab = (0.5, 0.5)
        self._last = (0.0, 0.0)
        self._watched: list[object] = []
        self._follow_screens()

    def _follow_screens(self) -> None:
        """A screen plugged in or out, resized or rescaled, or its taskbar moved or resized: the pill finds its place
        again, inside the work area."""
        from PySide6.QtGui import QGuiApplication

        app = QGuiApplication.instance()
        if app is None or self._in_window:
            return
        app.screenAdded.connect(self._screen_added)
        app.screenRemoved.connect(self._screens_changed)
        for screen in QGuiApplication.screens():
            self._watch(screen)

    def _watch(self, screen: object) -> None:
        if screen in self._watched:
            return
        self._watched.append(screen)
        screen.geometryChanged.connect(self._screens_changed)
        screen.availableGeometryChanged.connect(self._screens_changed)

    def _screen_added(self, screen: object) -> None:
        self._watch(screen)
        self._screens_changed()

    def _screens_changed(self, *screen: object) -> None:
        from PySide6.QtGui import QGuiApplication

        there = QGuiApplication.screens()
        self._watched = [watched for watched in self._watched if watched in there]
        self._found = None
        found = self._all()
        self._place = read(asdict(self._place), found, next(iter(found)))
        self.changed.emit()

    def _all(self) -> dict[str, Rect]:
        if self._in_window:
            return {"": self._area}  # one window: points only, nothing beside it
        if self._found is None:
            self._found = self._screens()  # asks the taskbar too: not on every move of a drag
        return self._found

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

    def _held(self, x: float, y: float) -> Held:
        return Held(x, y, self._grab[0], self._grab[1], self._sizes)

    def shown(self) -> Place:
        return self._preview if self._dragging else self._place

    def _shown_screen(self) -> Rect:
        if self._dragging:
            return self._preview_screen
        return self._screen(self._place.screen)

    def _get_edge(self) -> str:
        return self.shown().edge

    def _get_form(self) -> str:
        return form_of(self.shown().edge)

    def _get_floating(self) -> bool:
        return self.shown().floating

    def _get_dragging(self) -> bool:
        return self._dragging

    def _get_screen(self) -> dict:
        return box_of(self._shown_screen())

    def _get_work(self) -> dict:
        return box_of(work_of(self._shown_screen()))

    def _get_snaps(self) -> list:
        """While dragging: the nearest edge's corners and centre (their middles), the one it's pulled onto marked."""
        if not self._dragging:
            return []
        area = work_of(self._preview_screen)
        edge = self._near
        width, height = self._sizes[form_of(edge)]
        spots = []
        for along in SPOTS:
            box = spot(area, edge, along, width, height)
            spots.append(
                {
                    "x": box.x + box.width / 2,
                    "y": box.y + box.height / 2,
                    "on": not self._preview.floating and along == self._preview.along,
                }
            )
        return spots

    def _get_landing(self) -> dict:
        """While dragging to an edge: the middle of where the pill lands if let go now; empty while it would float."""
        if not self._dragging or self._preview.floating:
            return {}
        area = work_of(self._preview_screen)
        edge = self._preview.edge
        width, height = self._sizes[form_of(edge)]
        box = spot(area, edge, self._preview.along, width, height)
        return {"x": box.x + box.width / 2, "y": box.y + box.height / 2}

    def _get_near(self) -> str:
        return self._near if self._dragging else ""

    def _get_line(self) -> float:
        return float_line(work_of(self._preview_screen)) if self._dragging else 0.0

    edge = Property(str, _get_edge, notify=changed)
    form = Property(str, _get_form, notify=changed)
    floating = Property(bool, _get_floating, notify=changed)
    dragging = Property(bool, _get_dragging, notify=dragChanged)
    screen = Property("QVariantMap", _get_screen, notify=changed)  # all of it: where a pill tucks away past
    work = Property("QVariantMap", _get_work, notify=changed)  # its work area: where pills sit
    snaps = Property(list, _get_snaps, notify=changed)
    landing = Property("QVariantMap", _get_landing, notify=changed)
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
        """The pill's size in a form, for where it lands and the spots shown while it's dragged."""
        self._sizes[form] = (width, height)

    @Slot(str, result="QVariantMap")
    def sizeOf(self, form: str) -> dict:
        """The pill's size in a form, as last told (or a likely one)."""
        width, height = self._sizes.get(form, SIZES["row"])
        return {"width": width, "height": height}

    @Slot(float, float)
    def holdAt(self, grab_x: float, grab_y: float) -> None:
        """Where the mouse holds the pill, as shares of its size: it lands where it's let go, held there."""
        self._grab = (min(1.0, max(0.0, grab_x)), min(1.0, max(0.0, grab_y)))

    @Slot(result="QPointF")
    def cursor(self) -> QPointF:
        """The mouse, in global points: read here, since the pill's window moves under it while it's dragged."""
        from PySide6.QtGui import QCursor

        return QPointF(QCursor.pos())

    @Slot(float, float)
    def begin(self, x: float, y: float) -> None:
        self._found = None  # a taskbar set to hide itself since, which Qt doesn't say
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
        self._last = (x, y)
        self._preview_screen = screen
        self._near = nearest_edge(work_of(screen), x, y, edges)
        self._preview = drop(self._place, name, screen, edges, self._held(x, y))
        self.changed.emit()

    @Slot()
    def end(self) -> None:
        if not self._dragging:
            return
        self.move(*self._last)  # once more, with the size the pill has taken in its new form
        self._place = self._preview
        self._dragging = False
        self._grab = (0.5, 0.5)
        self._save()
        self.dragChanged.emit()
        self.changed.emit()

    @Slot()
    def cancel(self) -> None:
        if not self._dragging:
            return
        self._dragging = False
        self._grab = (0.5, 0.5)
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
        area = work_of(self._shown_screen())
        if place.floating:
            box = floating_spot(area, place.x, place.y, width, height)
        else:
            box = spot(area, place.edge, place.along, width, height)
        return {"x": box.x, "y": box.y}

    def _save(self) -> None:
        if self._keep:
            ui_settings.set_value(KEY + self._name, asdict(self._place))
