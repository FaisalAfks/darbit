"""The panel darbit's tray icon opens (TrayPanel.qml): the running bots with their controls, the tools, Open darbit
Studio and Quit. `TrayPanel` carries what only app.py can do (open the Studio, record, quit); `panel_place` puts the
panel by the icon on whichever edge of the screen the taskbar is.
"""

from PySide6.QtCore import QObject, QPoint, QRect, QSize, Signal, Slot

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
