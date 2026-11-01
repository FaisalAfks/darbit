"""Open darbit Studio: the window, darbit's icon, and the tray. `darbit app` calls `main()`.

The Studio is a client of darbit's service (started in the background if it isn't running), so closing it
stops nothing: running bots go on. `shot()` draws a page into a PNG with no screen, for docs and tests.
"""

import sys
from collections.abc import Callable
from pathlib import Path

from PySide6.QtCore import Q_ARG, QMetaObject, QObject, QRect, Qt, QTimer, QUrl, Signal
from PySide6.QtGui import QGuiApplication, QIcon
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtQuick import QQuickWindow
from PySide6.QtWidgets import QApplication, QMenu, QSystemTrayIcon

from ..platform import system
from ..server import ui_settings
from ..service.client import Client
from .backend import Studio
from .capture import Capture, ShotProvider
from .ghost import Ghost
from .highlight import Highlight
from .recorder import Recorder
from .runpill import RunPill
from .window import PLACE, Door, fit, kept, screens

HERE = Path(__file__).parent
MAIN = HERE / "qml" / "Main.qml"
ICON = HERE / "darbit.ico"  # every size Windows asks for: taskbar, tray, Alt+Tab, shortcuts
APP_ID = "darbit.studio"  # Windows' name for the Studio: its taskbar button is its own, not python.exe's
SHOT_WAIT_MS = 1500  # time for the pages to get their data and draw before a shot
HIDE_WAIT_MS = 250  # time for the Studio to leave the screen before Capture grabs it


def _client() -> Client:
    return Client("darbit Studio")


def load(
    studio: Studio,
    capture: Capture | None = None,
    recorder: Recorder | None = None,
    highlight: Highlight | None = None,
    ghost: Ghost | None = None,
    run_pill: RunPill | None = None,
    place: tuple[QRect | None, bool] = (None, False),
) -> QQmlApplicationEngine:
    """The QML engine with the Studio's window loaded and shown (at `place`: where, and maximized or not);
    RuntimeError if the QML doesn't load."""
    engine = QQmlApplicationEngine()
    if capture is None:
        capture = Capture(ShotProvider())
    if recorder is None:
        recorder = Recorder()
    if highlight is None:
        highlight = Highlight()
    if ghost is None:
        ghost = Ghost()
    if run_pill is None:
        run_pill = RunPill()
    engine.addImageProvider("capture", capture.provider)
    engine.rootContext().setContextProperty("studio", studio)
    engine.rootContext().setContextProperty("capture", capture)
    engine.rootContext().setContextProperty("recorder", recorder)
    engine.rootContext().setContextProperty("highlight", highlight)
    engine.rootContext().setContextProperty("ghost", ghost)
    engine.rootContext().setContextProperty("runPill", run_pill)
    studio.setParent(engine)  # the engine outlives its windows, so these do too: no binding sees them gone
    capture.setParent(engine)
    recorder.setParent(engine)
    highlight.setParent(engine)
    ghost.setParent(engine)
    run_pill.setParent(engine)
    engine.load(QUrl.fromLocalFile(str(MAIN)))
    if not engine.rootObjects():
        raise RuntimeError("darbit Studio's window didn't load: see the QML errors above")
    window = engine.rootObjects()[0]
    where, maximized = place
    if where is not None:
        window.setGeometry(where)
    if maximized:
        window.showMaximized()
    else:
        window.show()
    return engine


def main(argv: list[str] | None = None, connect: Callable[[], Client] = _client) -> int:
    system.name_app(APP_ID)  # before any window, or Windows has already grouped it with python.exe
    app = QApplication(argv if argv is not None else sys.argv)
    app.setApplicationName("darbit Studio")
    app.setDesktopFileName("darbit")
    app.setWindowIcon(QIcon(str(ICON)))
    door = Door()
    if door.knock():
        return 0  # the open Studio comes forward instead
    door.open()
    studio = Studio(connect)
    capture = Capture(ShotProvider())
    recorder = Recorder()
    highlight = Highlight()
    ghost = Ghost()
    run_pill = RunPill()
    engine = load(studio, capture, recorder, highlight, ghost, run_pill, fit(ui_settings.get(PLACE), screens()))
    _connect_ghost(studio, ghost)
    window = engine.rootObjects()[0]
    _connect_highlight(studio, highlight, window)
    keys = _global_keys(
        {"highlight.toggle": studio.toggleHighlight, "capture.freeze": lambda: _capture_now(studio, capture)}
    )
    _connect_capture(studio, capture, recorder, window)
    _connect_recorder(studio, capture, recorder, window)
    _connect_run_pill(studio, run_pill, window)

    def open_studio() -> None:
        run_pill.close()  # the Studio comes back in its place
        _bring_forward(window)

    tray = _tray(app, open_studio)
    door.knocked.connect(open_studio)
    _keep_in_tray(app, window, tray)
    code = app.exec()
    door.close()
    highlight.stop()
    ghost.stop()
    run_pill.close()
    recorder.close()
    if keys is not None:
        keys[0].stop()
    tray.hide()
    return code


def _connect_capture(studio: Studio, capture: Capture, recorder: Recorder, window: object) -> None:
    """Capture hides the Studio, grabs the screen without it, and brings it back when it closes."""

    def wanted(folder: str, mode: str, name: str, kind: str) -> None:
        window.hide()
        QTimer.singleShot(HIDE_WAIT_MS, lambda: capture.start(Path(folder), mode, name, kind))

    def closed() -> None:
        if not capture.isOpen and not recorder.active:  # while recording, the recorder comes back instead
            _bring_forward(window)
            studio.loadLibrary()

    studio.captureWanted.connect(wanted)
    capture.openChanged.connect(closed)
    capture.saved.connect(lambda name: studio.loadLibrary())


def _connect_recorder(studio: Studio, capture: Capture, recorder: Recorder, window: object) -> None:
    """Record hides the Studio and shows the recorder; Done brings it back. A picture check is taken with Capture."""
    wanted_gone: list[bool] = []  # a picture check waiting for Capture's save: until it's gone?

    def record(folder: str, name: str, again: bool) -> None:
        window.hide()

        def start() -> None:
            problem = recorder.start(Path(folder), name, again)
            if problem:
                _bring_forward(window)
                studio.say(problem)

        QTimer.singleShot(HIDE_WAIT_MS, start)

    def finished(name: str) -> None:
        _bring_forward(window)
        studio.loadActions()
        studio.loadLibrary()
        studio.say(f"Saved {name}" if name else "Recording thrown away")

    def picture(folder: str, gone: bool) -> None:
        wanted_gone[:] = [gone]
        capture.start(Path(folder), "any")

    def saved(name: str) -> None:
        if recorder.active and wanted_gone:
            recorder.addPicture(name, wanted_gone[0])
            wanted_gone.clear()
            capture.close()

    studio.recordWanted.connect(record)
    recorder.finished.connect(finished)
    recorder.pictureWanted.connect(picture)
    capture.saved.connect(saved)


def _connect_run_pill(studio: Studio, run_pill: RunPill, window: object) -> None:
    """Play hides the Studio behind the run pill; the bot stopping or failing, or the pill's ⤢, brings it back."""
    seen_running: list[bool] = []  # the bot ran since Play: until then, "stopped" is the status from before

    def started() -> None:
        if studio.runPill:
            seen_running.clear()
            window.hide()
            run_pill.open()

    def status() -> None:
        if not run_pill.isOpen:
            return
        state = studio.bot.get("status")
        if state in ("running", "paused"):
            seen_running[:] = [True]
        elif state == "failed" or seen_running:
            run_pill.close()

    studio.started.connect(started)
    studio.botChanged.connect(status)
    run_pill.closed.connect(lambda: _bring_forward(window))


def _connect_ghost(studio: Studio, ghost: Ghost) -> None:
    """The ghost cursor listens while its setting is on."""

    def follow() -> None:
        if studio.ghost:
            ghost.start()
        else:
            ghost.stop()

    studio.lookChanged.connect(follow)
    follow()


def _connect_highlight(studio: Studio, highlight: Highlight, window: object) -> None:
    """Highlight hides the Studio while it's on; Ctrl+Alt+H turns it on and off with the game in front."""

    def toggle(folder: str, name: str) -> None:
        if highlight.isOn:
            highlight.stop()
            _bring_forward(window)
        else:
            window.hide()
            QTimer.singleShot(HIDE_WAIT_MS, lambda: highlight.start(Path(folder), only=name))

    studio.highlightWanted.connect(toggle)


def _capture_now(studio: Studio, capture: Capture) -> None:
    """Ctrl+Alt+C with the game in front: Capture on the screen as it is (unless it's open already)."""
    if not capture.isOpen:
        studio.openCapture("any")


class _Key(QObject):
    """A global key's press, as a signal: pressed on the hotkeys' thread, handled on the window's."""

    pressed = Signal()


def _global_keys(slots: dict[str, Callable[[], None]]) -> tuple[object, list[_Key]] | None:
    """Call each action's function when its global key (from the user's keymap) is pressed; None without any."""
    from .. import keymap
    from ..platform import hotkeys
    from ..platform.backend import NotSupported

    combos = {}
    handlers = {}
    kept = []
    for action, slot in slots.items():
        combo = keymap.combo(action)
        if not combo:
            continue
        key = _Key()
        key.pressed.connect(
            slot, Qt.ConnectionType.QueuedConnection
        )  # pressed on the hotkeys' thread, run on the window's
        combos[action] = combo
        handlers[action] = key.pressed.emit
        kept.append(key)
    if not combos:
        return None
    try:
        registered = hotkeys.register(combos, handlers)
    except NotSupported:
        return None
    return registered, kept


def _tray(app: QApplication, open_studio: Callable[[], None]) -> QSystemTrayIcon:
    tray = QSystemTrayIcon(QIcon(str(ICON)), app)
    tray.setToolTip("darbit Studio")
    menu = QMenu()
    menu.addAction("Open darbit Studio", open_studio)
    menu.addSeparator()
    menu.addAction("Quit (bots go on)", app.quit)
    tray.setContextMenu(menu)
    tray.activated.connect(lambda reason: open_studio() if reason == QSystemTrayIcon.Trigger else None)
    if QSystemTrayIcon.isSystemTrayAvailable():
        tray.show()
    return tray


TOLD = "studio.told_tray"  # ui setting: the tray message was shown once


def _keep_in_tray(app: QApplication, window: object, tray: QSystemTrayIcon) -> None:
    """Closing the window keeps darbit in the tray (Quit is in its menu), and the window's place is kept for next time.
    Without a tray, closing quits."""

    def remember() -> None:
        ui_settings.set_value(PLACE, kept(window, ui_settings.get(PLACE)))

    def closing() -> None:
        remember()
        if tray.isVisible() and not ui_settings.get(TOLD, False):
            tray.showMessage("darbit Studio is in the tray", "Bots go on. Open it or quit from here.", QIcon(str(ICON)))
            ui_settings.set_value(TOLD, True)

    app.setQuitOnLastWindowClosed(not tray.isVisible())
    window.closing.connect(closing)
    app.aboutToQuit.connect(lambda: remember() if window.isVisible() else None)


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
    action: str = "dim_run",
) -> None:
    """Draw one page of the Studio into a PNG, with no screen needed (QT_QPA_PLATFORM=offscreen)."""
    app = QGuiApplication.instance() or QGuiApplication([sys.argv[0]])
    studio = Studio(connect, theme, bot)
    engine = load(studio)
    window = engine.rootObjects()[0]
    if not isinstance(window, QQuickWindow):
        raise TypeError("darbit Studio's window isn't a Qt Quick window")
    window.resize(*size)
    if page == "action":  # the editor shows one action: open it
        QTimer.singleShot(
            SHOT_WAIT_MS // 3, lambda: QMetaObject.invokeMethod(window, "openAction", Q_ARG("QVariant", action))
        )
    else:
        QTimer.singleShot(SHOT_WAIT_MS // 3, lambda: QMetaObject.invokeMethod(window, "go", Q_ARG("QVariant", page)))

    def save() -> None:
        try:
            window.grabWindow().save(str(path))
        finally:
            app.quit()

    QTimer.singleShot(SHOT_WAIT_MS, save)
    app.exec()
    del engine
