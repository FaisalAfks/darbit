"""Open darbit Studio: the window, darbit's icon, and the tray. `darbit app` calls `main()`.

The Studio is a client of darbit's service (started in the background if it isn't running), so closing it to the
tray stops nothing; quitting stops the running bots unless darbit settings keep them going. `shot()` draws a page into
a PNG with no screen, for docs and tests.
"""

import sys
import time
from collections.abc import Callable
from pathlib import Path

from PySide6.QtCore import Q_ARG, QMetaObject, QObject, QRect, QSize, Qt, QTimer, QUrl, Signal
from PySide6.QtGui import QCursor, QGuiApplication, QIcon, QWindow
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtQuick import QQuickWindow
from PySide6.QtWidgets import QApplication, QSystemTrayIcon

from ..platform import system
from ..server import ui_settings
from ..service.client import Client
from .backend import Studio
from .capture import Capture, ShotProvider, saved_shot
from .docking import PillPlace
from .ghost import Ghost
from .hiding import HidingPill, told_by_window
from .recorder import Recorder
from .scout import Scout, ShotsProvider
from .tray import TrayPanel, panel_place
from .window import PLACE, Door, fit, kept, screens

HERE = Path(__file__).parent
MAIN = HERE / "qml" / "Main.qml"
ICON = HERE / "darbit.ico"  # every size Windows asks for: taskbar, tray, Alt+Tab, shortcuts
APP_ID = "darbit.studio"  # Windows' name for the Studio: its taskbar button is its own, not python.exe's
SHOT_WAIT_MS = 1500  # time for the pages to get their data and draw before a shot
HIDE_WAIT_MS = 250  # time for the Studio to leave the screen before Capture grabs it
PILLS = ("run", "recorder", "scout", "capture")  # every pill over the game: each keeps its own place (#384)


def _client() -> Client:
    """The real service, started in the background first if it isn't running. (Only here: a Studio given another
    connection, a test's or a probe's, never starts one.)"""
    from ..service.client import ensure_running

    ensure_running()
    return Client("darbit Studio")


def load(
    studio: Studio,
    capture: Capture | None = None,
    recorder: Recorder | None = None,
    scout: Scout | None = None,
    ghost: Ghost | None = None,
    run_pill: HidingPill | None = None,
    recorder_hiding: HidingPill | None = None,
    place: tuple[QRect | None, bool] = (None, False),
    scout_hiding: HidingPill | None = None,
    pill_places: dict[str, PillPlace] | None = None,
    capture_hiding: HidingPill | None = None,
    tray_panel: TrayPanel | None = None,
) -> QQmlApplicationEngine:
    """The QML engine with the Studio's window loaded and shown (at `place`: where, and maximized or not);
    RuntimeError if the QML doesn't load. `pill_places` are the pills' places by name (run, recorder, scout,
    capture), each made here when not given."""
    engine = QQmlApplicationEngine()
    if capture is None:
        capture = Capture(ShotProvider())
    if recorder is None:
        recorder = Recorder()
    if scout is None:
        scout = Scout()
    if ghost is None:
        ghost = Ghost()
    if run_pill is None:
        run_pill = HidingPill()
    if recorder_hiding is None:
        recorder_hiding = HidingPill()
    if scout_hiding is None:
        scout_hiding = HidingPill()
    if capture_hiding is None:
        capture_hiding = HidingPill(watch=told_by_window)
    if tray_panel is None:
        tray_panel = TrayPanel()
    places = dict(pill_places or {})
    for name in PILLS:
        if name not in places:
            places[name] = PillPlace(name, in_window=name == "capture")
    engine.addImageProvider("capture", capture.provider)
    engine.addImageProvider("scout", ShotsProvider(scout.shots))  # the engine owns it
    engine.rootContext().setContextProperty("studio", studio)
    engine.rootContext().setContextProperty("capture", capture)
    engine.rootContext().setContextProperty("recorder", recorder)
    engine.rootContext().setContextProperty("scout", scout)
    engine.rootContext().setContextProperty("ghost", ghost)
    engine.rootContext().setContextProperty("runPill", run_pill)
    engine.rootContext().setContextProperty("recorderHiding", recorder_hiding)
    engine.rootContext().setContextProperty("scoutHiding", scout_hiding)
    engine.rootContext().setContextProperty("captureHiding", capture_hiding)
    engine.rootContext().setContextProperty("trayPanel", tray_panel)
    for name, pill_place in places.items():
        engine.rootContext().setContextProperty(name + "Place", pill_place)
        pill_place.setParent(engine)
    studio.setParent(engine)  # the engine outlives its windows, so these do too: no binding sees them gone
    capture.setParent(engine)
    recorder.setParent(engine)
    scout.setParent(engine)
    ghost.setParent(engine)
    run_pill.setParent(engine)
    recorder_hiding.setParent(engine)
    scout_hiding.setParent(engine)
    capture_hiding.setParent(engine)
    tray_panel.setParent(engine)
    _connect_scout_hiding(scout, scout_hiding)
    _connect_capture_hiding(capture, capture_hiding)
    _connect_recorder_hiding(
        recorder, capture, recorder_hiding
    )  # here, so the recorder's pill works wherever it's loaded
    engine.load(QUrl.fromLocalFile(str(MAIN)))
    if not engine.rootObjects():
        raise RuntimeError("darbit Studio's window didn't load: see the QML errors above")
    window = engine.rootObjects()[0]
    _release_when_hidden(window)
    where, maximized = place
    if where is not None:
        window.setGeometry(where)
    if maximized:
        window.showMaximized()
    else:
        window.show()
    return engine


def _release_when_hidden(root: QQuickWindow) -> None:
    """Every window gives back its graphics memory while it's hidden: the Studio is hidden for as long as a bot runs,
    and Capture and Scout most of the time."""
    for window in [root, *root.findChildren(QQuickWindow)]:
        window.setPersistentGraphics(False)
        window.setPersistentSceneGraph(False)


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
    scout = Scout()
    ghost = Ghost()
    run_pill = HidingPill()
    recorder_hiding = HidingPill()
    place = fit(ui_settings.get(PLACE), screens())
    tray_panel = TrayPanel()
    engine = load(studio, capture, recorder, scout, ghost, run_pill, recorder_hiding, place, tray_panel=tray_panel)
    _connect_ghost(studio, ghost)
    window = engine.rootObjects()[0]
    _connect_scout(studio, scout, window)
    keys = _GlobalKeys({"scout.toggle": studio.toggleScout, "capture.freeze": lambda: _capture_now(studio, capture)})
    keys.register()
    studio.keysChanged.connect(keys.register)  # a key changed in darbit settings works at once
    stepping = _GlobalKeys({"scout.next": scout.next, "scout.previous": scout.previous})
    _step_while_scouting(scout, stepping, studio)
    _connect_capture(studio, capture, recorder, window, scout)
    _connect_recorder(studio, capture, recorder, window)
    _connect_run_pill(studio, run_pill, window)

    def open_studio() -> None:
        run_pill.close()  # the Studio comes back in its place
        _bring_forward(window)

    tray = _tray(app, studio, window, open_studio, tray_panel)
    studio.checksFound.connect(open_studio)  # Play from the tray with the Studio hidden: its checks show in it
    studio.askedToReplace.connect(open_studio)  # and so does the question before stopping a bot in the way
    door.knocked.connect(open_studio)
    _keep_in_tray(app, window, tray)
    _tell_from_tray(studio, tray, open_studio)
    code = app.exec()
    _stop_bots_on_quit(studio, window, tray)
    door.close()
    scout.stop()
    ghost.stop()
    run_pill.close()
    recorder_hiding.close()
    recorder.close()
    keys.stop()
    stepping.stop()
    tray.hide()
    return code


def _connect_capture(studio: Studio, capture: Capture, recorder: Recorder, window: object, scout: Scout) -> None:
    """Capture hides the Studio, grabs the screen without it, and brings it back when it closes. A retake from
    Scout's pill hides Scout instead, and Scout comes back after it."""
    scouting: list[str] = []  # the bot Scout was on for, to come back to

    def step_aside() -> None:
        window.hide()
        scouting.clear()
        if scout.isOn:
            scouting.append(scout.folder)
            scout.stop()

    def wanted(folder: str, mode: str, name: str, kind: str) -> None:
        step_aside()
        QTimer.singleShot(HIDE_WAIT_MS, lambda: capture.start(Path(folder), mode, name, kind))

    def wanted_on_shot(folder: str, name: str, kind: str, screenshot: str) -> None:
        found = saved_shot(Path(screenshot))
        if found is None:
            studio.say("That screenshot can't be used: the screens are laid out differently now")
            return
        step_aside()
        capture.start(
            Path(folder),
            "one",
            name,
            kind,
            shot=found.pixels,
            origin=found.origin,
            lossy=found.lossy,
            shot_id=found.shot_id,
        )

    def closed() -> None:
        if capture.isOpen:
            return
        if scouting:
            folder = Path(scouting.pop())
            QTimer.singleShot(HIDE_WAIT_MS, lambda: scout.start(folder, land_on=scout.landed))  # once Capture is gone
            studio.loadLibrary()
            return
        if not recorder.active:  # while recording, the recorder comes back instead
            _bring_forward(window)
            studio.loadLibrary()
            if studio.screens:  # the Screen view has been opened: a new shot may be there
                studio.loadScreens()

    studio.captureWanted.connect(wanted)
    studio.captureOnShotWanted.connect(wanted_on_shot)
    capture.openChanged.connect(closed)
    capture.saved.connect(lambda name: studio.loadLibrary())
    capture.saved.connect(scout.forget)  # taken again: Scout looks at it afresh


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
        capture.start(Path(folder), "any", several=False)  # the check waits for one image

    def saved(name: str) -> None:
        if recorder.active and wanted_gone:
            recorder.addPicture(name, wanted_gone[0])
            wanted_gone.clear()
            capture.close()

    studio.recordWanted.connect(record)
    recorder.finished.connect(finished)
    recorder.pictureWanted.connect(picture)
    capture.saved.connect(saved)


def _connect_recorder_hiding(recorder: Recorder, capture: Capture, hiding: HidingPill) -> None:
    """The recorder's pill hides like the run pill while a recording goes on (not while Capture takes an image)."""

    def follow() -> None:
        if recorder.active and not capture.isOpen:
            hiding.open()
        else:
            hiding.close()

    recorder.stateChanged.connect(follow)
    capture.openChanged.connect(follow)


def _connect_scout_hiding(scout: Scout, hiding: HidingPill) -> None:
    """Scout's pill shows while Scout is on, and hides like the run pill."""

    def follow() -> None:
        if scout.isOn:
            hiding.open()
        else:
            hiding.close()

    scout.changed.connect(follow)
    follow()


def _connect_capture_hiding(capture: Capture, hiding: HidingPill) -> None:
    """Capture's pill hides like the others while Capture is open; Capture's window tells it the mouse."""

    def follow() -> None:
        if capture.isOpen:
            hiding.open()
        else:
            hiding.close()

    capture.openChanged.connect(follow)


def _connect_run_pill(studio: Studio, run_pill: HidingPill, window: object) -> None:
    """The bot starting (from Play or anywhere else) hides the Studio behind the run pill; the bot stopping or
    failing, or the pill's ⤢, brings it back. Closing or minimizing the Studio with a bot running opens the pill
    too, and showing the Studio again closes it."""
    seen_running: list[bool] = []  # the bot ran since Play: until then, "stopped" is the status from before

    def started() -> None:
        if studio.runPill:
            seen_running.clear()
            window.hide()
            run_pill.open()

    last = {"path": None, "state": None}  # the shown bot's status as last seen

    def status() -> None:
        state = studio.bot.get("status")
        path = studio.bot.get("path")
        was = last["state"] if last["path"] == path else None
        last["path"], last["state"] = path, state
        if not run_pill.isOpen:
            # the bot started anywhere (Play, the tray, the command line, the service): the Studio steps aside too;
            # showing a bot that's already running doesn't count
            if was is not None and was not in ("running", "paused") and state == "running":
                started()
            return
        if state in ("running", "paused"):
            seen_running[:] = [True]
        elif state == "failed" or seen_running:
            run_pill.close()

    def out_of_sight() -> None:
        """The Studio closed to the tray or minimized: a bot running or paused stays in reach in the pill, the shown
        one first, else the first running one, which becomes the shown bot."""
        if not studio.runPill or run_pill.isOpen:
            return
        bot = _running_bot(studio)
        if bot is None:
            return
        if bot.get("path") != studio.bot.get("path"):
            studio.selectBot(str(bot.get("path")))
        seen_running[:] = [True]
        run_pill.open()

    def visibility(shown: QWindow.Visibility) -> None:
        if shown == QWindow.Minimized:
            out_of_sight()
        elif shown in IN_SIGHT and run_pill.isOpen:
            run_pill.close()  # the Studio is back (its taskbar button): the pill makes way

    studio.started.connect(started)
    studio.botChanged.connect(status)
    run_pill.closed.connect(lambda: _bring_forward(window))
    window.closing.connect(out_of_sight)
    window.visibilityChanged.connect(visibility)


IN_SIGHT = (QWindow.Windowed, QWindow.Maximized, QWindow.FullScreen)  # the Studio's window on screen


def _running_bot(studio: Studio) -> dict | None:
    """The bot running or paused: the shown one if it is, else the first other one; None when none is."""
    for bot in [studio.bot, *studio.bots]:
        if bot.get("status") in ("running", "paused"):
            return bot
    return None


def _connect_ghost(studio: Studio, ghost: Ghost) -> None:
    """The ghost cursor listens while its setting is on."""

    def follow() -> None:
        if studio.ghost:
            ghost.start()
        else:
            ghost.stop()

    studio.lookChanged.connect(follow)
    follow()


def _connect_scout(studio: Studio, scout: Scout, window: object) -> None:
    """Scout hides the Studio while it's on; its key turns it on and off with the game in front. From the Library
    or Results it lands on the image picked there."""

    def toggle(folder: str, name: str) -> None:
        if scout.isOn and not name:
            scout.stop()
            _bring_forward(window)
        elif scout.isOn:
            scout.landOn(name)
        else:
            window.hide()
            QTimer.singleShot(HIDE_WAIT_MS, lambda: scout.start(Path(folder), land_on=name))

    studio.scoutWanted.connect(toggle)


def _step_while_scouting(scout: Scout, stepping: "_GlobalKeys", studio: Studio) -> None:
    """N and Shift+N step through Scout's images while it's on, with the game in front; they're the game's again
    once it's hidden."""

    def follow() -> None:
        if scout.isOn and stepping.registered is None:
            stepping.register()
        elif not scout.isOn and stepping.registered is not None:
            stepping.stop()

    def keys_changed() -> None:
        if scout.isOn:
            stepping.register()

    scout.changed.connect(follow)
    studio.keysChanged.connect(keys_changed)


def _capture_now(studio: Studio, capture: Capture) -> None:
    """Ctrl+Alt+C with the game in front: Capture on the screen as it is (unless it's open already)."""
    if not capture.isOpen:
        studio.openCapture("any")


class _Key(QObject):
    """A global key's press, as a signal: pressed on the hotkeys' thread, handled on the window's."""

    pressed = Signal()


class _GlobalKeys:
    """Calls each action's function when its global key (from the user's keymap) is pressed."""

    def __init__(self, slots: dict[str, Callable[[], None]]) -> None:
        self.slots = slots
        self.registered: object | None = None
        self.kept: list[_Key] = []

    def register(self) -> None:
        """Register the keys as they are now, in place of any from before."""
        from .. import keymap
        from ..platform import hotkeys
        from ..platform.backend import NotSupported

        self.stop()
        combos = {}
        handlers = {}
        for action, slot in self.slots.items():
            combo = keymap.combo(action)
            if not combo:
                continue
            key = _Key()
            # pressed on the hotkeys' thread, run on the window's
            key.pressed.connect(slot, Qt.ConnectionType.QueuedConnection)
            combos[action] = combo
            handlers[action] = key.pressed.emit
            self.kept.append(key)
        if not combos:
            return
        try:
            self.registered = hotkeys.register(combos, handlers)
        except NotSupported:
            self.registered = None

    def stop(self) -> None:
        if self.registered is not None:
            self.registered.stop()
        self.registered = None
        self.kept = []


def _tray(
    app: QApplication, studio: Studio, window: object, open_studio: Callable[[], None], panel: TrayPanel
) -> QSystemTrayIcon:
    """darbit in the tray: a click on the icon opens the tray panel by it (the running bots, the tools, Open darbit
    Studio and Quit), a double click the Studio."""
    tray = QSystemTrayIcon(QIcon(str(ICON)), app)
    tray.setToolTip("darbit Studio")
    shown = window.findChild(QQuickWindow, "trayPanel")
    hidden_at = [0.0]  # when the panel last went away: a click on the icon that closed it doesn't open it again

    def place() -> None:
        icon = tray.geometry()
        if not icon.isValid() or icon.isEmpty():
            icon = QRect(QCursor.pos(), QSize(1, 1))
        screen = QGuiApplication.screenAt(icon.center()) or QGuiApplication.primaryScreen()
        size = QSize(shown.width(), shown.height())
        shown.setPosition(panel_place(icon, screen.geometry(), screen.availableGeometry(), size))

    def open_panel() -> None:
        if shown.isVisible() or time.monotonic() - hidden_at[0] < REOPEN_S:
            return
        place()
        shown.show()
        shown.raise_()
        shown.requestActivate()

    def visible(on: bool) -> None:
        if not on:
            hidden_at[0] = time.monotonic()

    def record() -> None:
        open_studio()
        QMetaObject.invokeMethod(window, "go", Q_ARG("QVariant", "library"))
        QMetaObject.invokeMethod(window, "recordAction", Q_ARG("QVariant", ""))

    def activated(reason: QSystemTrayIcon.ActivationReason) -> None:
        if reason == QSystemTrayIcon.DoubleClick:
            open_studio()
        elif reason in (QSystemTrayIcon.Trigger, QSystemTrayIcon.Context):
            open_panel()

    shown.visibleChanged.connect(visible)
    shown.heightChanged.connect(lambda height: place() if shown.isVisible() else None)  # grows from the taskbar
    panel.studioWanted.connect(open_studio)
    panel.recordWanted.connect(record)
    panel.quitWanted.connect(app.quit)
    tray.activated.connect(activated)
    if QSystemTrayIcon.isSystemTrayAvailable():
        tray.show()
    return tray


REOPEN_S = 0.3  # a click on the icon this soon after the panel closed was the click that closed it


def _stop_bots_on_quit(studio: Studio, window: object, tray: QSystemTrayIcon) -> None:
    """Quitting stops every running bot, cleanly through the service, unless darbit settings keep them going: with
    the Studio gone nothing would be left to control them. The window and the icon go first, so nothing hangs on
    screen while they stop."""
    if studio.keepBots:
        return
    window.hide()
    tray.hide()
    studio.stop_every_bot()


TOLD = "studio.told_tray"  # ui setting: the tray message was shown once


def _tell_from_tray(studio: Studio, tray: QSystemTrayIcon, open_studio: Callable[[], None]) -> None:
    """What needs the person while the Studio is out of sight (an image that may have stopped matching) comes as a
    Windows notification; clicking it opens the Studio."""

    def tell(title: str, text: str) -> None:
        if tray.isVisible():
            tray.showMessage(title, text, QIcon(str(ICON)), TELL_MS)

    studio.pictureFailing.connect(tell)
    tray.messageClicked.connect(open_studio)


TELL_MS = 15000  # how long a notification from the tray stays


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
