"""What darbit Studio's pages bind to: the bots, the chosen one and its pages' data, from darbit's service.

Every request to the service goes on a worker thread, and its answer comes back to the window's thread as a
signal, so the window never waits. The service's events (a bot started, its report grew) reload what they touch.
The Studio holds no state of its own about bots: closing it loses nothing.
"""

import shutil
import subprocess
import threading
import time
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from PySide6.QtCore import Property, QObject, QTimer, QUrl, Signal, Slot
from PySide6.QtGui import QDesktopServices

from .. import keymap, paths
from ..platform import system
from ..server import ui_settings
from ..service.client import Client, ServiceError
from . import shortcuts, theme

CHOSEN = "studio.bot"  # ui setting: the bot shown last
THEME = "theme"  # ui setting: the theme, shared with the old Studio
PICKER = "studio.picker"  # ui setting: "dropdown" (the default) or "sidebar"
EFFECTS = "studio.effects"  # ui setting: smooth effects (motion and glass); off for slower PCs
LAYOUT = "studio.layout"  # ui setting prefix: the person's own Overview layout for a bot, by the bot's folder
GHOST = "studio.ghost"  # ui setting: the ghost cursor, what bots click and press shown over the game
RUN_PILL = "studio.run_pill"  # ui setting: Play hides the Studio and shows the run pill
KEEP_BOTS = "studio.keep_bots"  # ui setting: quitting the Studio leaves running bots running
BLUR_THROUGH = "studio.blur_through"  # ui setting: pages blur through and cards tilt in as a page changes
AURORA = "studio.aurora"  # ui setting: a slow colour drift behind the glass, never on battery
BATTERY_EVERY_MS = 60_000  # how often the aurora asks whether the PC runs on its battery
RUNNING = ("running", "paused")  # a bot's states while it runs


@dataclass
class Undo:
    """How to take back a delete or rename: the request, and what the Library reads again after it."""

    method: str
    params: dict
    then: str  # "changed" (the assets) or "actionsChanged"
    was: str  # the name it has until it's taken back ("" for a delete)
    now: str  # the name it has again
    bot: str = ""  # the bot's folder it was done to


@dataclass
class Offer:
    """A change done, what the toast says about it, and its Undo."""

    said: str
    undo: Undo


class Studio(QObject):
    """The service, as properties and slots for QML."""

    botsChanged = Signal()
    botChanged = Signal()
    overviewChanged = Signal()
    checksChanged = Signal()
    checksFound = Signal()  # Play's checks found a problem: the Studio shows them, with Start anyway
    inTheWayChanged = Signal()
    askedToReplace = Signal()  # a start refused for a bot that sends input running: the Studio asks to stop it
    pictureFailing = Signal(str, str)  # (title, text): an image may have stopped matching, for the tray to say
    libraryChanged = Signal()
    screensChanged = Signal()
    daysChanged = Signal()
    dayChanged = Signal()
    settingsChanged = Signal()
    messageChanged = Signal()
    busyChanged = Signal()
    themeChanged = Signal()
    clockChanged = Signal()
    usesChanged = Signal()
    quitChanged = Signal()  # what quitting does with the running bots changed (the tray panel's Quit)
    keysChanged = Signal()  # a key changed: app.py registers the global ones again
    lookChanged = Signal()
    motionChanged = Signal()  # effects turned on or off, or the window came into sight or left it
    batteryChanged = Signal()
    liveChanged = Signal()
    started = Signal()  # the bot started from Play: app.py hides the Studio behind the run pill
    madeBot = Signal(str)  # a bot made, installed or added: its name
    actionsChanged = Signal()
    actionChanged = Signal()  # the action open in the editor
    playingChanged = Signal()  # the action playing and its line, as the service plays it
    said = Signal(str)  # something done, for the toast
    offered = Signal(str)  # something done that Undo takes back (undoLast), for the toast with its Undo
    undone = Signal(str, str)  # (the name it had, the name it has again): a rename taken back, for the Library
    scoutWanted = Signal(str, str)  # (the bot's folder, an image to land on or ""): Scout on or off, for app.py
    recordWanted = Signal(str, str, bool)  # (the bot's folder, the action's name, record it again), for app.py

    captureWanted = Signal(str, str, str, str)  # (the bot's folder, "any", "guide" or "one", name, kind), for app.py
    captureOnShotWanted = Signal(str, str, str, str)  # (the bot's folder, name, kind, a screenshot file), for app.py

    _answered = Signal(str, object)  # (what, result), from a worker thread
    _failed = Signal(str)
    _happened = Signal(str, object)  # (topic, data), from the client's reading thread

    def __init__(self, connect: Callable[[], Client], theme_name: str = "", bot: str = "") -> None:
        super().__init__()
        self._connect = connect
        self._client: Client | None = None
        self._bots: list[dict] = []
        self._bot: dict = {}
        self._overview: dict = {}  # the Overview as blocks: catalog, layout (the person's or the bot's), data
        self._checks: dict = {}  # darbit doctor's checks on a bot before Start: {bot, checks, problems}
        self._in_the_way: dict = {}  # a refused start or play, until Stop and start or Cancel
        self._told_failing: set[str] = set()  # images already said to be failing (bot, image, since)
        self._library: list[dict] = []
        self._screens: list[
            dict
        ] = []  # each screen's last shot with its targets in place, for the Library's Screen view
        self._library_bot = ""  # the bot the library was loaded for: until it's this one, the page says it's loading
        self._days: list[dict] = []
        self._day: dict = {}
        self._settings: dict = {}
        self._uses: list[dict] = []
        self._actions: list[dict] = []
        self._action: dict = {}
        self._playing = {"action": "", "line": 0, "status": ""}
        self._message = ""
        self._undo: Undo | None = None  # the last delete or rename, while the toast offers to take it back
        self._busy = 0
        self._wanted = bot or str(ui_settings.get(CHOSEN, ""))  # a bot's path or name to show first
        self._theme_name = theme_name or str(ui_settings.get(THEME, theme.DEFAULT))
        self._colors = theme.colors(self._theme_name, _custom_theme())
        # read once: the ghost cursor's marks read these several times a second while a bot runs
        self._sidebar = ui_settings.get(PICKER, "dropdown") == "sidebar"
        self._effects = bool(ui_settings.get(EFFECTS, True))
        self._ghost = bool(ui_settings.get(GHOST, True))
        self._run_pill = bool(ui_settings.get(RUN_PILL, True))
        self._keep_bots = bool(ui_settings.get(KEEP_BOTS, False))
        self._blur_through = bool(ui_settings.get(BLUR_THROUGH, False))
        self._aurora = bool(ui_settings.get(AURORA, False))
        self._shown = True  # the Studio's window on screen: not hidden, not minimized
        self._motion = theme.motion(self._effects)
        self._live: dict = {}  # where the bot is and its round, from the latest Overview: the run pill shows these
        self._waiting: dict | None = None  # an Overview that came while the window was out of sight
        self._battery = False
        self._battery_check = QTimer(self)
        self._battery_check.setInterval(BATTERY_EVERY_MS)
        self._battery_check.timeout.connect(self._check_battery)
        # read once and when one changes: every shortcut in the window reads these
        self._keys = shortcuts.now()
        self._key_rows = shortcuts.rows()
        self._answered.connect(self._take)
        self._failed.connect(self._show_failure)
        self._happened.connect(self._on_event)

    # ---- properties

    def _get_bots(self) -> list:
        return self._bots

    def _get_bot(self) -> dict:
        return self._bot

    def _get_overview(self) -> dict:
        return self._overview

    def _get_checks(self) -> dict:
        return self._checks

    def _get_in_the_way(self) -> dict:
        return self._in_the_way

    def _get_running(self) -> list:
        return [bot for bot in self._bots if bot.get("status") in RUNNING]

    def _get_library(self) -> list:
        return self._library

    def _get_screens(self) -> list:
        return self._screens

    def _get_library_ready(self) -> bool:
        return bool(self._bot.get("path")) and self._library_bot == self._bot.get("path")

    def _get_days(self) -> list:
        return self._days

    def _get_day(self) -> dict:
        return self._day

    def _get_settings(self) -> dict:
        return self._settings

    def _get_message(self) -> str:
        return self._message

    def _get_busy(self) -> bool:
        return self._busy > 0

    def _get_colors(self) -> dict:
        return self._colors

    def _get_theme(self) -> str:
        return self._theme_name

    def _get_glass(self) -> bool:
        return theme.blurs(self._theme_name)

    def _get_now(self) -> float:
        return time.time()

    def _get_keys(self) -> dict:
        return self._keys

    def _get_key_rows(self) -> list:
        return self._key_rows

    def _keys_changed(self) -> None:
        self._keys = shortcuts.now()
        self._key_rows = shortcuts.rows()
        self.keysChanged.emit()

    def _get_uses(self) -> list:
        return self._uses

    def _get_actions(self) -> list:
        return self._actions

    def _get_action(self) -> dict:
        return self._action

    def _get_playing(self) -> dict:
        return self._playing

    def _get_sidebar(self) -> bool:
        return self._sidebar

    def _get_effects(self) -> bool:
        return self._effects

    def _get_ghost(self) -> bool:
        return self._ghost

    def _get_motion(self) -> dict:
        return self._motion

    def _get_pill_motion(self) -> dict:
        return theme.motion(self._effects)

    def _get_blur_through(self) -> bool:
        return self._blur_through

    def _get_aurora(self) -> bool:
        return self._aurora

    def _get_battery(self) -> bool:
        return self._battery

    def _get_shown(self) -> bool:
        return self._shown

    def _get_live(self) -> dict:
        return self._live

    def _get_run_pill(self) -> bool:
        return self._run_pill

    def _get_keep_bots(self) -> bool:
        return self._keep_bots

    def _get_quit_label(self) -> str:
        return quit_label(self.running_names(), self._keep_bots)

    def _get_symbols(self) -> str:
        return symbol_font()

    def _get_desktop_origin(self) -> list:
        """Where the desktop starts: a bot's screenshot is the whole desktop, and matches are in screen pixels."""
        from ..platform import screen
        from ..platform.backend import NotSupported

        try:
            area = screen.desktop()
        except (NotSupported, OSError):
            return [0, 0]
        return [area.x, area.y]

    def _get_version(self) -> str:
        from .. import __version__

        return __version__

    bots = Property(list, _get_bots, notify=botsChanged)
    bot = Property(dict, _get_bot, notify=botChanged)
    overview = Property(
        dict, _get_overview, notify=overviewChanged
    )  # {catalog, layout, botLayout, custom, data, problem}
    checks = Property(
        dict, _get_checks, notify=checksChanged
    )  # {bot, checks: [{name, ok, found, fix, missing}], problems}
    # a refused start or action play: {path, name, what, method, params, running: [{name, path, status, input,
    # action}]}, the bots (or an action playing) in the way
    inTheWay = Property(dict, _get_in_the_way, notify=inTheWayChanged)
    running = Property(list, _get_running, notify=botsChanged)  # every bot running or paused, each with `input`
    library = Property(list, _get_library, notify=libraryChanged)
    screens = Property(list, _get_screens, notify=screensChanged)
    libraryReady = Property(bool, _get_library_ready, notify=libraryChanged)
    days = Property(list, _get_days, notify=daysChanged)
    day = Property(dict, _get_day, notify=dayChanged)
    settings = Property(dict, _get_settings, notify=settingsChanged)
    message = Property(str, _get_message, notify=messageChanged)
    busy = Property(bool, _get_busy, notify=busyChanged)
    colors = Property(dict, _get_colors, notify=themeChanged)
    themeName = Property(str, _get_theme, notify=themeChanged)
    glass = Property(bool, _get_glass, notify=themeChanged)
    now = Property(float, _get_now, notify=clockChanged)
    uses = Property(list, _get_uses, notify=usesChanged)
    keys = Property(dict, _get_keys, notify=keysChanged)  # action -> keys ("ctrl+k"), for the Studio's shortcuts
    keyRows = Property(list, _get_key_rows, notify=keysChanged)  # for darbit settings
    actions = Property(list, _get_actions, notify=actionsChanged)
    action = Property(dict, _get_action, notify=actionChanged)
    playing = Property(dict, _get_playing, notify=playingChanged)  # {action, line, status}
    sidebar = Property(bool, _get_sidebar, notify=lookChanged)
    effects = Property(bool, _get_effects, notify=lookChanged)
    ghost = Property(bool, _get_ghost, notify=lookChanged)
    # the Studio window's motion tokens (theme.motion): every duration 0 while effects are off or the window is out of
    # sight, so nothing animates then
    motion = Property(dict, _get_motion, notify=motionChanged)
    pillMotion = Property(dict, _get_pill_motion, notify=lookChanged)  # the pills': they show while the Studio hides
    blurThrough = Property(bool, _get_blur_through, notify=lookChanged)
    aurora = Property(bool, _get_aurora, notify=lookChanged)
    onBattery = Property(bool, _get_battery, notify=batteryChanged)  # asked only while the aurora is on
    shown = Property(bool, _get_shown, notify=motionChanged)
    live = Property(dict, _get_live, notify=liveChanged)  # {now, round}: where the bot is, for the run pill
    runPill = Property(bool, _get_run_pill, notify=lookChanged)
    keepBots = Property(bool, _get_keep_bots, notify=lookChanged)  # quitting leaves running bots running
    quitLabel = Property(str, _get_quit_label, notify=quitChanged)  # Quit, saying what it does with running bots
    version = Property(str, _get_version, constant=True)
    desktopOrigin = Property(list, _get_desktop_origin, constant=True)  # [x, y], to place a match on a screenshot
    symbols = Property(str, _get_symbols, constant=True)  # the font for the icons drawn from symbols (◎ ● ▣ ⇅ ⌕)

    # ---- what the pages ask for

    @Slot()
    def connect(self) -> None:
        """Connect to the service (started in the background if needed) and load the bots."""
        self._run("connected", self._open)

    @Slot(str)
    def selectBot(self, path: str) -> None:
        for found in self._bots:
            if found.get("path") == path:
                self._bot = found
                ui_settings.set_value(CHOSEN, path)
                self.botChanged.emit()
                self.libraryChanged.emit()  # another bot's library isn't this one's
                if self._screens:  # nor its screens
                    self.loadScreens()
                self.loadOverview()
                return

    @Slot()
    def start(self) -> None:
        """Start the shown bot. One refused because a bot that sends input runs asks first (`askedToReplace`)."""
        self._ask_to_replace("started", "bot.start")

    @Slot()
    def replaceAndStart(self) -> None:
        """Stop and start (or play): what's in the way stops cleanly, then what was refused is asked for again."""
        asked = self._in_the_way
        self._set_in_the_way({})
        client = self._client
        if not asked or client is None:
            return
        params = {**asked["params"], "replace": True}
        self._run(asked["what"], lambda: client.call(asked["method"], bot=asked["path"], **params))

    def _ask_to_replace(self, what: str, method: str, **params: object) -> None:
        """A request for the shown bot that sends input (a start, an action's play): refused because a bot or an
        action that sends input runs, it's kept in `inTheWay` and the Studio asks whether to stop that first."""
        if not self._bot or self._client is None:
            return
        client = self._client
        bot = {"path": self._bot["path"], "name": self._bot.get("name", "")}

        def ask() -> object:
            try:
                return client.call(method, bot=bot["path"], **params)
            except ServiceError as error:
                if error.code != "input_bot_running":
                    raise
                running = list(error.detail.get("running", []))
                return {"refused": True, **bot, "what": what, "method": method, "params": params, "running": running}

        self._run(what, ask)

    @Slot()
    def keepRunning(self) -> None:
        """Cancel: the bots in the way go on, and the refused bot doesn't start."""
        self._set_in_the_way({})

    def _set_in_the_way(self, asked: dict) -> None:
        self._in_the_way = asked
        self.inTheWayChanged.emit()

    @Slot()
    def play(self) -> None:
        """Start the shown bot after darbit doctor's checks: at once when they find nothing, else `checksFound`, for
        the Studio to show what's wrong with Start anyway. A service that can't check starts it as before."""
        if not self._bot or self._client is None:
            return
        client = self._client
        bot = self._bot["path"]

        def check() -> dict:
            try:
                found = client.call("bot.doctor", bot=bot)
            except ServiceError:
                found = {"checks": [], "problems": 0}
            return {**found, "bot": bot}

        self._run("play", check)

    @Slot()
    def pause(self) -> None:
        self._ask("status", "bot.pause")

    @Slot()
    def stop(self) -> None:
        self._ask("status", "bot.stop")

    @Slot(str)
    def pauseBot(self, path: str) -> None:
        """Pause a running bot, or let a paused one go on: any bot, not only the shown one (the tray panel)."""
        self._ask_about(path, "bot.pause")

    @Slot(str)
    def stopBot(self, path: str) -> None:
        self._ask_about(path, "bot.stop")

    @Slot()
    def editBot(self) -> None:
        """Open the shown bot's folder in VS Code when it's installed, else in the file explorer."""
        folder = self._bot.get("path")
        if not folder:
            return
        code = shutil.which("code")
        if code:
            subprocess.Popen([code, folder], creationflags=system.no_window())
        else:
            QDesktopServices.openUrl(QUrl.fromLocalFile(folder))

    @Slot(str)
    def openCapture(self, mode: str) -> None:
        """Capture for the shown bot: anything, or the guide's pictures not taken yet."""
        if self._bot.get("path"):
            self.captureWanted.emit(self._bot["path"], mode, "", "image")

    @Slot(str, str)
    def retake(self, name: str, kind: str) -> None:
        """Capture one picture again, by its name."""
        if self._bot.get("path"):
            self.captureWanted.emit(self._bot["path"], "one", name, kind or "image")

    @Slot(str, str, str)
    def retakeOn(self, name: str, kind: str, screenshot: str) -> None:
        """Capture one target again on a saved screenshot instead of the screen now: a failure's, the one Scout last
        saw it on, or a screen's last shot in the Library (a file URL or a path)."""
        if not self._bot.get("path") or not screenshot:
            return
        path = QUrl(screenshot).toLocalFile() if screenshot.startswith("file:") else screenshot
        self.captureOnShotWanted.emit(self._bot["path"], name, kind or "image", path)

    @Slot()
    def loadActions(self) -> None:
        self._ask("actions", "bot.actions")

    @Slot(str)
    def openAction(self, name: str) -> None:
        """Read an action into the editor."""
        self._ask("action", "bot.action.read", name=name)

    @Slot(str, "QVariantList")
    def saveAction(self, name: str, sections: list) -> None:
        """Write the editor's sections and steps back to the action's file."""
        self._ask("action", "bot.action.save", name=name, sections=list(sections))

    @Slot(str)
    def playAction(self, name: str) -> None:
        self._ask_to_replace("played", "bot.action.play", name=name)

    @Slot()
    def stopAction(self) -> None:
        self._ask("", "bot.action.stop")

    @Slot(str)
    def stepThroughAction(self, name: str) -> None:
        """Play an action stopping at its first line, for Next line and Go on."""
        self._ask_to_replace("", "bot.action.play", name=name, stepping=True)

    @Slot()
    def resumeAction(self) -> None:
        self._ask("", "bot.action.resume")

    @Slot()
    def stepAction(self) -> None:
        self._ask("", "bot.action.step")

    @Slot(str, "QVariantList")
    def setBreakpoints(self, name: str, lines: list) -> None:
        """Stop at these lines of the action (kept beside the bot, never in its file)."""
        kept = sorted({int(line) for line in lines})
        self._action = {**self._action, "breakpoints": kept}
        self.actionChanged.emit()
        self._ask("", "bot.action.breakpoints", name=name, lines=kept)

    @Slot(str, str)
    def renameAction(self, name: str, to: str) -> None:
        back = Undo("bot.action.rename", {"name": to, "to": name}, "actionsChanged", to, name)
        self._ask_undoable(f"Renamed {name} to {to}", back, "bot.action.rename", name=name, to=to)

    @Slot(str)
    def deleteAction(self, name: str) -> None:
        back = Undo("bot.library.undelete", {}, "actionsChanged", "", name)
        self._ask_undoable(f"Deleted {name}", back, "bot.action.delete", name=name)

    @Slot(str, bool)
    def record(self, name: str, again: bool) -> None:
        """Record an action for the shown bot (app.py hides the Studio and shows the recorder)."""
        if self._bot.get("path"):
            self.recordWanted.emit(self._bot["path"], name, again)

    @Slot()
    def toggleScout(self) -> None:
        """Scout every image of the bot on screen, or stop."""
        if self._bot.get("path"):
            self.scoutWanted.emit(self._bot["path"], "")

    @Slot(str)
    def scoutOne(self, name: str) -> None:
        """Scout, landed on one image (from the Library or Results)."""
        if self._bot.get("path"):
            self.scoutWanted.emit(self._bot["path"], name)

    def _take_overview(self, result: dict) -> None:
        """A new Overview. The run pill's line and the tray's warning need it even while the window is out of sight;
        the Overview page waits until the window is back (drawing it again then would be for nothing)."""
        data = result.get("data") if isinstance(result.get("data"), dict) else {}
        self._live = {"now": data.get("now"), "round": data.get("round")}
        self.liveChanged.emit()
        self._tell_failing(data.get("failing"))
        if not self._shown:
            self._waiting = result
            return
        self._waiting = None
        self._show_overview(result)

    def _show_overview(self, result: dict) -> None:
        mine = ui_settings.get(f"{LAYOUT}:{self._bot.get('path', '')}")
        bot_layout = list(result.get("layout", []))
        self._overview = {
            **result,
            "botLayout": bot_layout,
            "layout": mine if isinstance(mine, list) else bot_layout,
            "custom": isinstance(mine, list),
        }
        self.overviewChanged.emit()

    def _tell_failing(self, failing: object) -> None:
        """Say once (per image and since when) that an image may have stopped matching."""
        if not isinstance(failing, dict) or not failing.get("target"):
            return
        key = f"{self._bot.get('path', '')}|{failing['target']}|{failing.get('since')}"
        if key in self._told_failing:
            return
        self._told_failing.add(key)
        name = self._bot.get("name") or "The bot"
        self.pictureFailing.emit(
            f"{name}: {failing['target']} may have stopped matching", str(failing.get("sentence", ""))
        )

    @Slot(str)
    def say(self, text: str) -> None:
        self.said.emit(text)

    @Slot(str)
    def loadUses(self, name: str) -> None:
        self._uses = []
        self.usesChanged.emit()
        self._ask("uses", "bot.library.uses", name=name)

    @Slot(str, str)
    def renameAsset(self, name: str, to: str) -> None:
        back = Undo("bot.library.rename", {"name": to, "to": name}, "changed", to, name)
        self._ask_undoable(f"Renamed {name} to {to}", back, "bot.library.rename", name=name, to=to)

    @Slot(str)
    def deleteAsset(self, name: str) -> None:
        back = Undo("bot.library.undelete", {}, "changed", "", name)
        self._ask_undoable(f"Deleted {name}", back, "bot.library.delete", name=name)

    @Slot()
    def undoLast(self) -> None:
        """Take back the last delete or rename offered with Undo, on the bot it was done to."""
        back = self._undo
        self._undo = None
        if back is None or self._client is None:
            return
        client = self._client

        def work() -> object:
            client.call(back.method, bot=back.bot, **back.params)
            return back

        self._run("undone", work)

    def _reload(self, what: str) -> None:
        """The Library's assets ("changed") or its actions ("actionsChanged") read again."""
        if what == "changed":
            self.loadLibrary()
        else:
            self.loadActions()

    def _ask_undoable(self, said: str, back: Undo, method: str, **params: object) -> None:
        """A change to the shown bot that the toast then offers to take back."""
        if not self._bot or self._client is None:
            return
        client = self._client
        back.bot = self._bot["path"]

        def work() -> object:
            client.call(method, bot=back.bot, **params)
            return Offer(said, back)

        self._run("offered", work)

    @Slot(str)
    def newBot(self, name: str) -> None:
        """Make a bot from darbit's template, in darbit's bots folder."""
        self._everyone("made", "bots.new", name=name)

    @Slot(str)
    def installBot(self, url: str) -> None:
        self._everyone("made", "bots.install", url=url)

    @Slot(str)
    def addBot(self, path: str) -> None:
        self._everyone("made", "bots.add", path=_local_path(path))

    @Slot(str, str)
    def setKey(self, action: str, keys: str) -> None:
        """Change an action's keys, unless something else already has them."""
        taken = shortcuts.clash(action, keys)
        if taken:
            self._show_failure(f"{keys} is already {taken}: change that one first")
            return
        keymap.set_key(action, keys)
        self._keys_changed()

    @Slot(str)
    def resetKey(self, action: str) -> None:
        default = next(row["default"] for row in shortcuts.rows() if row["action"] == action)
        taken = shortcuts.clash(action, default)
        if taken:
            self._show_failure(f"{default} is now {taken}: change that one first")
            return
        keymap.reset_key(action)
        self._keys_changed()

    @Slot(bool)
    def setSidebar(self, on: bool) -> None:
        self._sidebar = bool(on)
        ui_settings.set_value(PICKER, "sidebar" if on else "dropdown")
        self.lookChanged.emit()

    @Slot(bool)
    def setEffects(self, on: bool) -> None:
        self._effects = bool(on)
        ui_settings.set_value(EFFECTS, self._effects)
        self.lookChanged.emit()
        self._motion_changed()

    @Slot(bool)
    def setBlurThrough(self, on: bool) -> None:
        self._blur_through = bool(on)
        ui_settings.set_value(BLUR_THROUGH, self._blur_through)
        self.lookChanged.emit()

    @Slot(bool)
    def setAurora(self, on: bool) -> None:
        self._aurora = bool(on)
        ui_settings.set_value(AURORA, self._aurora)
        self.lookChanged.emit()
        self._follow_battery()

    @Slot(bool)
    def setShown(self, shown: bool) -> None:
        """The window came into sight (shown, restored) or left it (hidden, minimized). Out of sight nothing moves
        and the Overview waits; back in sight it shows the latest one."""
        if bool(shown) == self._shown:
            return
        self._shown = bool(shown)
        self._motion_changed()
        self._follow_battery()
        if self._shown and self._waiting is not None:
            waiting = self._waiting
            self._waiting = None
            self._show_overview(waiting)

    def _motion_changed(self) -> None:
        self._motion = theme.motion(self._effects and self._shown)
        self.motionChanged.emit()

    def _follow_battery(self) -> None:
        """Ask about the battery now and then, only while the aurora could show."""
        if self._aurora and self._shown:
            self._check_battery()
            self._battery_check.start()
        else:
            self._battery_check.stop()

    def _check_battery(self) -> None:
        on_battery = system.on_battery()
        if on_battery != self._battery:
            self._battery = on_battery
            self.batteryChanged.emit()

    @Slot(bool)
    def setGhost(self, on: bool) -> None:
        self._ghost = bool(on)
        ui_settings.set_value(GHOST, self._ghost)
        self.lookChanged.emit()

    @Slot(bool)
    def setRunPill(self, on: bool) -> None:
        self._run_pill = bool(on)
        ui_settings.set_value(RUN_PILL, self._run_pill)
        self.lookChanged.emit()

    @Slot(bool)
    def setKeepBots(self, on: bool) -> None:
        self._keep_bots = bool(on)
        ui_settings.set_value(KEEP_BOTS, self._keep_bots)
        self.lookChanged.emit()
        self.quitChanged.emit()

    def running_names(self) -> list[str]:
        """The names of the bots running or paused, as last heard from the service."""
        return [str(bot.get("name", "")) for bot in self._bots if bot.get("status") in RUNNING]

    def stop_every_bot(self) -> None:
        """Stop every bot running or paused, each cleanly through the service (it lets go of every key), and wait for
        them: the Studio is quitting. One that can't be stopped doesn't keep the others going; a service that's gone
        has nothing left to stop."""
        if self._client is None:
            return
        try:
            bots = self._client.call("bots.list")
        except ServiceError:
            return
        for bot in bots:
            if bot.get("status") not in RUNNING:
                continue
            try:
                self._client.call("bot.stop", bot=bot["path"])
            except ServiceError:
                continue

    @Slot()
    def checkBot(self) -> None:
        """Run darbit doctor's checks on the shown bot, in the service (a few seconds at most)."""
        if not self._bot or self._client is None:
            return
        client = self._client
        bot = self._bot["path"]
        self._run("checks", lambda: {**client.call("bot.doctor", bot=bot), "bot": bot})  # whose checks they are

    @Slot()
    def loadOverview(self) -> None:
        self._ask("overview", "bot.overview")

    @Slot("QVariantList")
    def saveLayout(self, blocks: list) -> None:
        """Keep the person's own Overview layout for the shown bot."""
        if not self._bot.get("path"):
            return
        kept = [dict(block) for block in blocks]
        ui_settings.set_value(f"{LAYOUT}:{self._bot['path']}", kept)
        self._overview = {**self._overview, "layout": kept, "custom": True}
        self.overviewChanged.emit()

    @Slot()
    def resetLayout(self) -> None:
        """Back to the bot's own Overview layout."""
        if not self._bot.get("path"):
            return
        ui_settings.set_value(f"{LAYOUT}:{self._bot['path']}", None)
        self._overview = {**self._overview, "layout": self._overview.get("botLayout", []), "custom": False}
        self.overviewChanged.emit()

    @Slot()
    def loadLibrary(self) -> None:
        self._ask("library", "bot.library")

    @Slot()
    def loadScreens(self) -> None:
        self._ask("screens", "bot.library.screens")

    @Slot()
    def loadDays(self) -> None:
        self._ask("days", "bot.days")

    @Slot(str)
    def loadDay(self, day: str) -> None:
        self._ask("day", "bot.day", day=day)

    @Slot()
    def loadSettings(self) -> None:
        self._ask("settings", "bot.settings")

    @Slot("QVariantMap")
    def saveSettings(self, values: dict) -> None:
        self._ask("saved", "bot.settings.save", values=dict(values))

    @Slot(str)
    def setTheme(self, name: str) -> None:
        """Use a theme from now on, and next time."""
        self._theme_name = name if name in theme.THEMES else theme.DEFAULT
        self._colors = theme.colors(self._theme_name, _custom_theme())
        ui_settings.set_value(THEME, self._theme_name)
        self.themeChanged.emit()

    @Slot()
    def tick(self) -> None:
        """Move the clock on (the run pill's time), once a second from QML."""
        self.clockChanged.emit()

    # ---- talking to the service

    def _open(self) -> object:
        if self._client is None:
            self._client = self._connect()
            self._client.on_event(self._from_service)
        return self._client.call("bots.list")

    def _ask(self, what: str, method: str, **params: object) -> None:
        if not self._bot or self._client is None:
            return
        client = self._client
        bot = self._bot["path"]
        self._run(what, lambda: client.call(method, bot=bot, **params))

    def _ask_about(self, bot: str, method: str) -> None:
        """A request about one bot, by its folder."""
        client = self._client
        if client is None or not bot:
            return
        self._run("status", lambda: client.call(method, bot=bot))

    def _everyone(self, what: str, method: str, **params: object) -> None:
        """A request about no bot in particular (making one)."""
        client = self._client
        if client is None:
            return
        self._run(what, lambda: client.call(method, **params))

    def _run(self, what: str, work: Callable[[], object]) -> None:
        self._busy += 1
        self.busyChanged.emit()

        def go() -> None:
            try:
                self._answered.emit(what, work())
            except ServiceError as error:
                self._failed.emit(str(error))
                self._answered.emit("", None)

        threading.Thread(target=go, name=f"darbit-studio-{what}", daemon=True).start()

    def _from_service(self, topic: str, data: dict) -> None:
        self._happened.emit(topic, data)

    @Slot(str, object)
    def _take(self, what: str, result: object) -> None:
        self._busy = max(0, self._busy - 1)
        self.busyChanged.emit()
        if what == "connected" and isinstance(result, list):
            self._set_bots(result)
        elif isinstance(result, dict) and result.get("refused"):
            self._set_in_the_way({key: value for key, value in result.items() if key != "refused"})
            self.askedToReplace.emit()
        elif what in ("status", "started"):
            if what == "started":
                self.started.emit()
            self._run("bots", lambda: self._client.call("bots.list") if self._client else [])
        elif what == "bots" and isinstance(result, list):
            self._set_bots(result)
        elif what == "play" and isinstance(result, dict):
            self._checks = result
            self.checksChanged.emit()
            if result.get("bot") != self._bot.get("path"):
                return  # another bot is shown by now: Play was for that one
            if result.get("problems"):
                self.checksFound.emit()
            else:
                self.start()
        elif what == "checks" and isinstance(result, dict):
            self._checks = result
            self.checksChanged.emit()
        elif what == "overview" and isinstance(result, dict):
            self._take_overview(result)
        elif what == "library" and isinstance(result, list):
            self._library = result
            self._library_bot = str(self._bot.get("path", ""))
            self.libraryChanged.emit()
        elif what == "screens" and isinstance(result, list):
            self._screens = result
            self.screensChanged.emit()
        elif what == "days" and isinstance(result, list):
            self._days = result
            self.daysChanged.emit()
        elif what == "day" and isinstance(result, dict):
            self._day = result
            self.dayChanged.emit()
        elif what == "settings" and isinstance(result, dict):
            self._settings = result
            self.settingsChanged.emit()
        elif what == "saved":
            self._show_failure("")
            self.loadSettings()
        elif what == "uses" and isinstance(result, list):
            self._uses = result
            self.usesChanged.emit()
        elif what == "changed":
            self.loadLibrary()
        elif what == "offered" and isinstance(result, Offer):
            self._undo = result.undo
            self._reload(result.undo.then)
            self.offered.emit(result.said)
        elif what == "undone" and isinstance(result, Undo):
            self._reload(result.then)
            self.undone.emit(result.was, result.now)
        elif what == "action" and isinstance(result, dict):
            self._action = result
            self.actionChanged.emit()
        elif what == "actions" and isinstance(result, list):
            self._actions = result
            self.actionsChanged.emit()
        elif what == "actionsChanged":
            self.loadActions()
        elif what == "played":
            self.said.emit("Playing: the Studio stays in front, so switch to the game")
        elif what == "made" and isinstance(result, dict):
            self._wanted = str(result.get("path", ""))
            self._bot = {}
            self.madeBot.emit(str(result.get("name", "")))
            self._run("bots", lambda: self._client.call("bots.list") if self._client else [])

    def _set_bots(self, found: list) -> None:
        self._bots = found
        self.botsChanged.emit()
        self.quitChanged.emit()
        chosen = None
        wanted = self._bot.get("path") or self._wanted
        for candidate in found:
            if wanted and wanted in (candidate.get("path"), candidate.get("name")):
                chosen = candidate
        if chosen is None and found:
            chosen = found[0]
        if chosen is not None:
            changed = chosen.get("path") != self._bot.get("path")
            self._bot = chosen
            self.botChanged.emit()
            if changed:
                self.libraryChanged.emit()
                self.loadOverview()

    @Slot(str)
    def _show_failure(self, text: str) -> None:
        self._message = text
        self.messageChanged.emit()

    @Slot(str, object)
    def _on_event(self, topic: str, data: object) -> None:
        if not isinstance(data, dict):
            return
        if topic == "project.status":
            self._run("bots", lambda: self._client.call("bots.list") if self._client else [])
        if topic == "project.changed" and data.get("path") == self._bot.get("path"):
            self.loadOverview()
        if topic in ("action.line", "action.paused"):
            self._playing = {"action": data.get("action", ""), "line": data.get("line", 0), "status": topic[7:]}
            self.playingChanged.emit()
        elif topic == "action.ended":
            self._playing = {"action": "", "line": 0, "status": str(data.get("status", "ended"))}
            self.playingChanged.emit()
            if data.get("status") not in (None, "ok", "stopped"):
                self.said.emit(
                    f"{data.get('action', 'The action')} stopped: {data.get('reason') or data.get('status')}"
                )


def quit_label(running: list[str], keep: bool) -> str:
    """Quit, saying what it does with the bots running (their names)."""
    if not running:
        return "Quit darbit Studio"
    if keep:
        return "Quit (bots go on)"
    if len(running) == 1:
        return f"Quit and stop {running[0]}"
    return f"Quit and stop {len(running)} bots"


def symbol_font() -> str:
    """The font the icons come from: on Windows, Segoe UI Symbol (Segoe UI's own fallback draws ⌕ ▣ ⇅ tiny);
    elsewhere the app's own font, which has them."""
    import sys

    if sys.platform == "win32":
        return "Segoe UI Symbol"
    from PySide6.QtGui import QGuiApplication

    return QGuiApplication.font().family()


def _local_path(text: str) -> str:
    """A folder from QML: a file:// URL or a plain path."""
    if text.startswith("file://"):
        from PySide6.QtCore import QUrl

        return QUrl(text).toLocalFile()
    return text


def _custom_theme() -> Path:
    """theme.toml in darbit's settings folder: tokens laid over a base theme."""
    return paths.config_dir() / "theme.toml"
