"""The panel darbit's tray icon opens (TrayPanel.qml): the running bots with their controls, the tools, Open darbit
Studio and Quit. `TrayPanel` carries what only app.py can do (open the Studio, record, quit); `panel_place` puts the
panel by the icon on whichever edge of the screen the taskbar is, inside the work area the pills use (docking.py),
never over the taskbar.
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


def icon_in_points(icon: QRect, screens: list[Rect]) -> QRect:
    """The tray icon's place in Qt's points. Windows tells it in its own pixels, which with display scaling lie past
    every screen in points (150%: the icon at pixel 1528 is at point 1018); those are brought back from the corner of
    the screen they're on, as Qt lays screens out."""
    centre = icon.center()
    for screen in screens:
        if holds(screen, centre.x(), centre.y()):
            return icon
    for screen in screens:
        if holds(in_pixels(screen), centre.x(), centre.y()):
            left = screen.x + (icon.x() - screen.x) / screen.ratio
            top = screen.y + (icon.y() - screen.y) / screen.ratio
            return QRect(
                round(left), round(top), round(icon.width() / screen.ratio), round(icon.height() / screen.ratio)
            )
    return icon


def screen_with(icon: QRect, screens: list[Rect]) -> Rect:
    """The screen the icon (in points) is on, or the first."""
    centre = icon.center()
    for screen in screens:
        if holds(screen, centre.x(), centre.y()):
            return screen
    return screens[0]


def panel_place(icon: QRect, screen: QRect, available: QRect, size: QSize) -> QPoint:
    """Where the panel's top left goes: beside the taskbar, lined up with the icon, and kept on the screen's free
    space."""
    edge = taskbar_edge(icon, screen, available)
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
