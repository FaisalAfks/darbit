"""The panel darbit's tray icon opens (TrayPanel.qml): the running bots with their controls, the tools, Open darbit
Studio and Quit. `TrayPanel` carries what only app.py can do (open the Studio, record, quit); `panel_place` puts the
panel by the icon on whichever edge of the screen the taskbar is, inside the work area the pills use (docking.py),
never over the taskbar, and outside the hidden-icons flyout when the icon is in it.
"""

from PySide6.QtCore import QObject, QPoint, QRect, QSize, Signal, Slot

from .docking import Rect, in_pixels

GAP = 8  # px between the panel and the taskbar


class TrayPanel(QObject):
    """The tray panel's buttons that app.py answers."""

    studioWanted = Signal()
    recordWanted = Signal()
    quitWanted = Signal()

    @Slot()
    def openStudio(self) -> None:
        self.studioWanted.emit()

    @Slot()
    def record(self) -> None:
        self.recordWanted.emit()

    @Slot()
    def quit(self) -> None:
        self.quitWanted.emit()


def taskbar_edge(icon: QRect, screen: QRect, available: QRect) -> str:
    """The screen edge the taskbar is on ("top", "bottom", "left" or "right"): the side the screen's free space
    leaves out, or, with a taskbar that hides itself, the side nearest the icon."""
    if available.bottom() < screen.bottom():
        return "bottom"
    if available.top() > screen.top():
        return "top"
    if available.left() > screen.left():
        return "left"
    if available.right() < screen.right():
        return "right"
    centre = icon.center()
    away = {
        "bottom": screen.bottom() - centre.y(),
        "top": centre.y() - screen.top(),
        "left": centre.x() - screen.left(),
        "right": screen.right() - centre.x(),
    }
    return min(away, key=lambda edge: away[edge])


def as_qrect(rect: Rect) -> QRect:
    return QRect(round(rect.x), round(rect.y), round(rect.width), round(rect.height))


def holds(rect: Rect, x: float, y: float) -> bool:
    return rect.x <= x < rect.right and rect.y <= y < rect.bottom


def pixel_screen(rect: QRect, screens: list[Rect]) -> Rect | None:
    """The screen whose pixels hold the middle of this rectangle Windows told in pixels, or None when it already lies
    on a screen in points (no display scaling there)."""
    centre = rect.center()
    for screen in screens:
        if holds(screen, centre.x(), centre.y()):
            return None
    for screen in screens:
        if holds(in_pixels(screen), centre.x(), centre.y()):
            return screen
    return None


def in_points(rect: QRect, screen: Rect | None) -> QRect:
    """A rectangle in Windows' pixels on this screen, in Qt's points: brought back from the screen's corner, as Qt
    lays screens out. None leaves it as it is."""
    if screen is None:
        return rect
    left = screen.x + (rect.x() - screen.x) / screen.ratio
    top = screen.y + (rect.y() - screen.y) / screen.ratio
    return QRect(round(left), round(top), round(rect.width() / screen.ratio), round(rect.height() / screen.ratio))


def icon_in_points(icon: QRect, screens: list[Rect]) -> QRect:
    """The tray icon's place in Qt's points. Windows tells it in its own pixels, which with display scaling lie past
    every screen in points (150%: the icon at pixel 1528 is at point 1018)."""
    return in_points(icon, pixel_screen(icon, screens))


def flyout_taken(icon: QRect, flyout: QRect | None, screens: list[Rect]) -> QRect | None:
    """The hidden-icons flyout's place in Qt's points when the icon (both in Windows' pixels) is in it, the room the
    panel must leave free; None when there's no flyout or the icon is on the taskbar itself."""
    if flyout is None or not flyout.contains(icon.center()):
        return None
    return in_points(flyout, pixel_screen(icon, screens))


def screen_with(icon: QRect, screens: list[Rect]) -> Rect:
    """The screen the icon (in points) is on, or the first."""
    centre = icon.center()
    for screen in screens:
        if holds(screen, centre.x(), centre.y()):
            return screen
    return screens[0]


def panel_place(icon: QRect, screen: QRect, available: QRect, size: QSize, taken: QRect | None = None) -> QPoint:
    """Where the panel's top left goes: beside the taskbar, lined up with the icon, and kept on the screen's free
    space. With `taken` (the hidden-icons flyout the icon is in) it goes past the flyout, away from the taskbar, or
    beside it when there's no room there."""
    edge = taskbar_edge(icon, screen, available)
    spot = by_taskbar(edge, icon, available, size)
    if taken is None or not QRect(spot, size).intersects(taken):
        return spot
    for other in outside(edge, taken, spot, size, available):
        if fits(QRect(other, size), available, taken):
            return other
    return spot


def by_taskbar(edge: str, icon: QRect, available: QRect, size: QSize) -> QPoint:
    """The panel's top left beside the taskbar on `edge`, lined up with the icon, kept on the free space."""
    centre = QPoint(icon.x() + icon.width() // 2, icon.y() + icon.height() // 2)
    if edge in ("top", "bottom"):
        x = centre.x() - size.width() // 2
        y = available.top() + GAP if edge == "top" else available.bottom() + 1 - GAP - size.height()
    else:
        y = centre.y() - size.height() // 2
        x = available.left() + GAP if edge == "left" else available.right() + 1 - GAP - size.width()
    x = max(available.left() + GAP, min(x, available.right() + 1 - GAP - size.width()))
    y = max(available.top() + GAP, min(y, available.bottom() + 1 - GAP - size.height()))
    return QPoint(x, y)


def outside(edge: str, taken: QRect, spot: QPoint, size: QSize, available: QRect) -> list[QPoint]:
    """Places for the panel clear of `taken`: past it, away from the taskbar, then on either side of it along the
    taskbar, the side with more room first."""
    if edge in ("top", "bottom"):
        past = taken.top() - GAP - size.height() if edge == "bottom" else taken.bottom() + 1 + GAP
        before = QPoint(taken.left() - GAP - size.width(), spot.y())
        after = QPoint(taken.right() + 1 + GAP, spot.y())
        more_before = taken.center().x() - available.left() > available.right() - taken.center().x()
        sides = [before, after] if more_before else [after, before]
        return [QPoint(spot.x(), past)] + sides
    past = taken.left() - GAP - size.width() if edge == "right" else taken.right() + 1 + GAP
    before = QPoint(spot.x(), taken.top() - GAP - size.height())
    after = QPoint(spot.x(), taken.bottom() + 1 + GAP)
    more_before = taken.center().y() - available.top() > available.bottom() - taken.center().y()
    sides = [before, after] if more_before else [after, before]
    return [QPoint(past, spot.y())] + sides


def fits(panel: QRect, available: QRect, taken: QRect) -> bool:
    """Whether the panel lies on the free space, GAP in from its edges, and off `taken`."""
    inside = available.adjusted(GAP, GAP, -GAP, -GAP).contains(panel)
    return inside and not panel.intersects(taken)
