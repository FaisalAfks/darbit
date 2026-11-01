"""What darbit Studio's pages bind to: the bots, the chosen one and its pages' data, from darbit's service.

Every request to the service goes on a worker thread, and its answer comes back to the window's thread as a
signal, so the window never waits. The service's events (a bot started, its report grew) reload what they touch.
The Studio holds no state of its own about bots: closing it loses nothing.
"""

import threading
import time
from collections.abc import Callable
from pathlib import Path

from PySide6.QtCore import Property, QObject, Signal, Slot

from .. import paths
from ..server import ui_settings
from ..service.client import Client, ServiceError
from . import theme

CHOSEN = "studio.bot"  # ui setting: the bot shown last
THEME = "theme"  # ui setting: the theme, shared with the old Studio
PICKER = "studio.picker"  # ui setting: "dropdown" (the default) or "sidebar"
EFFECTS = "studio.effects"  # ui setting: smooth effects (motion and glass); off for slower PCs
GHOST = "studio.ghost"  # ui setting: the ghost cursor, what bots click and press shown over the game


class Studio(QObject):
    """The service, as properties and slots for QML."""

    botsChanged = Signal()
    botChanged = Signal()
    overviewChanged = Signal()
    libraryChanged = Signal()
    daysChanged = Signal()
    dayChanged = Signal()
    settingsChanged = Signal()
    messageChanged = Signal()
    busyChanged = Signal()
    themeChanged = Signal()
    clockChanged = Signal()
    usesChanged = Signal()
    lookChanged = Signal()
    madeBot = Signal(str)  # a bot made, installed or added: its name
    actionsChanged = Signal()
    actionChanged = Signal()  # the action open in the editor
    playingChanged = Signal()  # the action playing and its line, as the service plays it
    said = Signal(str)  # something done, for the toast
    highlightWanted = Signal(str)  # the bot's folder: turn Highlight on or off, for app.py
    recordWanted = Signal(str, str, bool)  # (the bot's folder, the action's name, record it again), for app.py

    captureWanted = Signal(str, str, str, str)  # (the bot's folder, "any", "guide" or "one", name, kind), for app.py

    _answered = Signal(str, object)  # (what, result), from a worker thread
    _failed = Signal(str)
    _happened = Signal(str, object)  # (topic, data), from the client's reading thread

    def __init__(self, connect: Callable[[], Client], theme_name: str = "", bot: str = "") -> None:
        super().__init__()
        self._connect = connect
        self._client: Client | None = None
        self._bots: list[dict] = []
        self._bot: dict = {}
        self._overview: list[dict] = []
        self._library: list[dict] = []
        self._library_bot = ""  # the bot the library was loaded for: until it's this one, the page says it's loading
        self._days: list[dict] = []
        self._day: dict = {}
        self._settings: dict = {}
        self._uses: list[dict] = []
        self._actions: list[dict] = []
        self._action: dict = {}
        self._playing = {"action": "", "line": 0, "status": ""}
        self._message = ""
        self._busy = 0
        self._wanted = bot or str(ui_settings.get(CHOSEN, ""))  # a bot's path or name to show first
        self._theme_name = theme_name or str(ui_settings.get(THEME, theme.DEFAULT))
        self._colors = theme.colors(self._theme_name, _custom_theme())
        self._answered.connect(self._take)
        self._failed.connect(self._show_failure)
        self._happened.connect(self._on_event)

    # ---- properties

    def _get_bots(self) -> list:
        return self._bots

    def _get_bot(self) -> dict:
        return self._bot

    def _get_overview(self) -> list:
        return self._overview

    def _get_library(self) -> list:
        return self._library

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

    def _get_uses(self) -> list:
        return self._uses

    def _get_actions(self) -> list:
        return self._actions

    def _get_action(self) -> dict:
        return self._action

    def _get_playing(self) -> dict:
        return self._playing

    def _get_sidebar(self) -> bool:
        return ui_settings.get(PICKER, "dropdown") == "sidebar"

    def _get_effects(self) -> bool:
        return bool(ui_settings.get(EFFECTS, True))

    def _get_ghost(self) -> bool:
        return bool(ui_settings.get(GHOST, True))

    def _get_symbols(self) -> str:
        return symbol_font()

    def _get_version(self) -> str:
        from .. import __version__

        return __version__

    bots = Property(list, _get_bots, notify=botsChanged)
    bot = Property(dict, _get_bot, notify=botChanged)
    overview = Property(list, _get_overview, notify=overviewChanged)
    library = Property(list, _get_library, notify=libraryChanged)
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
    actions = Property(list, _get_actions, notify=actionsChanged)
    action = Property(dict, _get_action, notify=actionChanged)
    playing = Property(dict, _get_playing, notify=playingChanged)  # {action, line, status}
    sidebar = Property(bool, _get_sidebar, notify=lookChanged)
    effects = Property(bool, _get_effects, notify=lookChanged)
    ghost = Property(bool, _get_ghost, notify=lookChanged)
    version = Property(str, _get_version, constant=True)
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
                self.loadOverview()
                return

    @Slot()
    def start(self) -> None:
        self._ask("status", "bot.start")

    @Slot()
    def pause(self) -> None:
        self._ask("status", "bot.pause")

    @Slot()
    def stop(self) -> None:
        self._ask("status", "bot.stop")

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
        self._ask("played", "bot.action.play", name=name)

    @Slot()
    def stopAction(self) -> None:
        self._ask("", "bot.action.stop")

    @Slot(str, str)
    def renameAction(self, name: str, to: str) -> None:
        self._ask("actionsChanged", "bot.action.rename", name=name, to=to)

    @Slot(str)
    def deleteAction(self, name: str) -> None:
        self._ask("actionsChanged", "bot.action.delete", name=name)

    @Slot(str, bool)
    def record(self, name: str, again: bool) -> None:
        """Record an action for the shown bot (app.py hides the Studio and shows the recorder)."""
        if self._bot.get("path"):
            self.recordWanted.emit(self._bot["path"], name, again)

    @Slot()
    def toggleHighlight(self) -> None:
        """Highlight the shown bot's pictures on screen, or stop."""
        if self._bot.get("path"):
            self.highlightWanted.emit(self._bot["path"])

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
        self._ask("changed", "bot.library.rename", name=name, to=to)

    @Slot(str)
    def deleteAsset(self, name: str) -> None:
        self._ask("changed", "bot.library.delete", name=name)

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

    @Slot(bool)
    def setSidebar(self, on: bool) -> None:
        ui_settings.set_value(PICKER, "sidebar" if on else "dropdown")
        self.lookChanged.emit()

    @Slot(bool)
    def setEffects(self, on: bool) -> None:
        ui_settings.set_value(EFFECTS, bool(on))
        self.lookChanged.emit()

    @Slot(bool)
    def setGhost(self, on: bool) -> None:
        ui_settings.set_value(GHOST, bool(on))
        self.lookChanged.emit()

    @Slot()
    def loadOverview(self) -> None:
        self._ask("overview", "bot.dashboard")

    @Slot()
    def loadLibrary(self) -> None:
        self._ask("library", "bot.library")

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
            from ..service.client import ensure_running

            ensure_running()
            self._client = self._connect()
            self._client.on_event(self._from_service)
        return self._client.call("bots.list")

    def _ask(self, what: str, method: str, **params: object) -> None:
        if not self._bot or self._client is None:
            return
        client = self._client
        bot = self._bot["path"]
        self._run(what, lambda: client.call(method, bot=bot, **params))

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
        elif what == "status":
            self._run("bots", lambda: self._client.call("bots.list") if self._client else [])
        elif what == "bots" and isinstance(result, list):
            self._set_bots(result)
        elif what == "overview" and isinstance(result, dict):
            self._overview = list(result.get("tiles", []))
            self.overviewChanged.emit()
        elif what == "library" and isinstance(result, list):
            self._library = result
            self._library_bot = str(self._bot.get("path", ""))
            self.libraryChanged.emit()
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
