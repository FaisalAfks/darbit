"""Open darbit Studio: the window, darbit's icon, and the tray. `darbit app` calls `main()`.

The Studio is a client of darbit's service (started in the background if it isn't running), so closing it
stops nothing: running bots go on. `shot()` draws a page into a PNG with no screen, for docs and tests.
"""

import sys
from collections.abc import Callable
from pathlib import Path

from PySide6.QtCore import Q_ARG, QMetaObject, QTimer, QUrl
from PySide6.QtGui import QGuiApplication, QIcon
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtQuick import QQuickWindow
from PySide6.QtWidgets import QApplication, QMenu, QSystemTrayIcon

from ..service.client import Client
from .backend import Studio
from .capture import Capture, ShotProvider

HERE = Path(__file__).parent
MAIN = HERE / "qml" / "Main.qml"
ICON = HERE / "logo.png"
SHOT_WAIT_MS = 1500  # time for the pages to get their data and draw before a shot
HIDE_WAIT_MS = 250  # time for the Studio to leave the screen before Capture grabs it


def _client() -> Client:
    return Client("darbit Studio")


def load(studio: Studio, capture: Capture | None = None) -> QQmlApplicationEngine:
    """The QML engine with the Studio's window loaded; RuntimeError if the QML doesn't load."""
    engine = QQmlApplicationEngine()
    if capture is None:
        capture = Capture(ShotProvider())
    engine.addImageProvider("capture", capture.provider)
    engine.rootContext().setContextProperty("studio", studio)
    engine.rootContext().setContextProperty("capture", capture)
    studio.setParent(engine)  # the engine outlives its windows, so these do too: no binding sees them gone
    capture.setParent(engine)
    engine.load(QUrl.fromLocalFile(str(MAIN)))
    if not engine.rootObjects():
        raise RuntimeError("darbit Studio's window didn't load: see the QML errors above")
    return engine


def main(argv: list[str] | None = None, connect: Callable[[], Client] = _client) -> int:
    app = QApplication(argv if argv is not None else sys.argv)
    app.setApplicationName("darbit Studio")
    app.setDesktopFileName("darbit")
    app.setWindowIcon(QIcon(str(ICON)))
    studio = Studio(connect)
    capture = Capture(ShotProvider())
    engine = load(studio, capture)
    window = engine.rootObjects()[0]
    _connect_capture(studio, capture, window)
    tray = _tray(app, window)
    code = app.exec()
    tray.hide()
    return code


def _connect_capture(studio: Studio, capture: Capture, window: object) -> None:
    """Capture hides the Studio, grabs the screen without it, and brings it back when it closes."""

    def wanted(folder: str, mode: str, name: str, kind: str) -> None:
        window.hide()
        QTimer.singleShot(HIDE_WAIT_MS, lambda: capture.start(Path(folder), mode, name, kind))

    def closed() -> None:
        if not capture.isOpen:
            _bring_forward(window)
            studio.loadLibrary()

    studio.captureWanted.connect(wanted)
    capture.openChanged.connect(closed)
    capture.saved.connect(lambda name: studio.loadLibrary())


def _tray(app: QApplication, window: object) -> QSystemTrayIcon:
    tray = QSystemTrayIcon(QIcon(str(ICON)), app)
    tray.setToolTip("darbit Studio")
    menu = QMenu()
    menu.addAction("Open darbit Studio", lambda: _bring_forward(window))
    menu.addSeparator()
    menu.addAction("Quit (bots go on)", app.quit)
    tray.setContextMenu(menu)
    tray.activated.connect(lambda reason: _bring_forward(window) if reason == QSystemTrayIcon.Trigger else None)
    if QSystemTrayIcon.isSystemTrayAvailable():
        tray.show()
    return tray


def _bring_forward(window: object) -> None:
    window.show()
    window.raise_()
    window.requestActivate()


def shot(
    path: Path,
    page: str = "overview",
    theme: str = "glass-dark",
    size: tuple[int, int] = (1400, 880),
    bot: str = "",
    connect: Callable[[], Client] = _client,
) -> None:
    """Draw one page of the Studio into a PNG, with no screen needed (QT_QPA_PLATFORM=offscreen)."""
    app = QGuiApplication.instance() or QGuiApplication([sys.argv[0]])
    studio = Studio(connect, theme, bot)
    engine = load(studio)
    window = engine.rootObjects()[0]
    if not isinstance(window, QQuickWindow):
        raise TypeError("darbit Studio's window isn't a Qt Quick window")
    window.resize(*size)
    QTimer.singleShot(SHOT_WAIT_MS // 3, lambda: QMetaObject.invokeMethod(window, "go", Q_ARG("QVariant", page)))

    def save() -> None:
        try:
            window.grabWindow().save(str(path))
        finally:
            app.quit()

    QTimer.singleShot(SHOT_WAIT_MS, save)
    app.exec()
    del engine
