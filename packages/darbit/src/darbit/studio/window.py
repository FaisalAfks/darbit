"""darbit Studio's window between starts (#247): where it was and its size, kept in darbit's ui settings, and one
Studio at a time: a second `darbit app` brings the open one forward instead of opening another.
"""

import getpass

from PySide6.QtCore import QObject, QRect, Signal
from PySide6.QtGui import QGuiApplication
from PySide6.QtNetwork import QLocalServer, QLocalSocket

PLACE = "studio.window"  # ui setting: {x, y, width, height, maximized}
SIZE = (1400, 880)  # the first start's size
SMALLEST = (900, 600)  # Main.qml's minimum
SEEN = 120  # pixels of the window that must be on a screen for its old place to be used


def fit(place: object, screens: list[QRect]) -> tuple[QRect | None, bool]:
    """Where the window opens: its kept place on the screen it was on, made to fit that screen, or None (the system
    picks) when nothing was kept or that screen is gone. And whether it was maximized."""
    if not isinstance(place, dict):
        return None, False
    try:
        x, y = int(place["x"]), int(place["y"])
        width, height = int(place["width"]), int(place["height"])
    except (KeyError, TypeError, ValueError):
        return None, False
    maximized = bool(place.get("maximized", False))
    for screen in screens:
        overlap = screen.intersected(QRect(x, y, width, height))
        if overlap.width() >= SEEN and overlap.height() >= SEEN:
            width = max(SMALLEST[0], min(width, screen.width()))
            height = max(SMALLEST[1], min(height, screen.height()))
            x = min(max(x, screen.left()), screen.right() + 1 - width)
            y = min(max(y, screen.top()), screen.bottom() + 1 - height)
            return QRect(x, y, width, height), maximized
    return None, maximized


def screens() -> list[QRect]:
    """Every screen's room for windows (without the taskbar)."""
    return [screen.availableGeometry() for screen in QGuiApplication.screens()]


def kept(window: object, before: object) -> dict:
    """The place to keep for the window now. A maximized window keeps the size it had before, to go back to."""
    from PySide6.QtGui import QWindow

    if window.visibility() == QWindow.Visibility.Maximized:
        place = dict(before) if isinstance(before, dict) else {"x": 0, "y": 0, "width": SIZE[0], "height": SIZE[1]}
        place["maximized"] = True
        return place
    return {"x": window.x(), "y": window.y(), "width": window.width(), "height": window.height(), "maximized": False}


def door_name() -> str:
    return f"darbit-studio-{getpass.getuser()}"


class Door(QObject):
    """One Studio at a time: `knock()` tells an open Studio to come forward; `open()` listens for knocks."""

    knocked = Signal()

    def __init__(self, name: str = "") -> None:
        super().__init__()
        self._name = name or door_name()
        self._server: QLocalServer | None = None

    def knock(self) -> bool:
        """True if a Studio was open and was told to come forward."""
        socket = QLocalSocket()
        socket.connectToServer(self._name)
        if not socket.waitForConnected(500):
            return False
        socket.write(b"show")
        socket.waitForBytesWritten(500)
        socket.disconnectFromServer()
        return True

    def open(self) -> bool:
        server = QLocalServer(self)
        if not server.listen(self._name):
            QLocalServer.removeServer(self._name)  # left by a Studio that crashed (Linux and macOS)
            if not server.listen(self._name):
                return False
        server.newConnection.connect(self._answer)
        self._server = server
        return True

    def close(self) -> None:
        if self._server is not None:
            self._server.close()
            self._server = None

    def _answer(self) -> None:
        while self._server is not None and self._server.hasPendingConnections():
            self._server.nextPendingConnection().deleteLater()
            self.knocked.emit()
