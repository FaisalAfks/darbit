"""What darbit Studio's pages bind to: the bots, the chosen one and its pages' data, from darbit's service.

Every request to the service goes on a worker thread, and its answer comes back to the window's thread as a
signal, so the window never waits. The service's events (a bot started, its report grew) reload what they touch.
The Studio holds no state of its own about bots: closing it loses nothing.
"""

import threading
import time
from collections.abc import Callable

from PySide6.QtCore import Property, QObject, Signal, Slot

from ..server import ui_settings
from ..service.client import Client, ServiceError
from . import theme

CHOSEN = "studio.bot"  # ui setting: the bot shown last

PAGES = ("overview", "library", "runs", "settings")


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

    captureWanted = Signal(str, str)  # (the bot's folder, what to take: "any" or "guide"), for app.py

    _answered = Signal(str, object)  # (what, result), from a worker thread
    _failed = Signal(str)
    _happened = Signal(str, object)  # (topic, data), from the client's reading thread

    def __init__(self, connect: Callable[[], Client], theme_name: str = theme.DEFAULT, bot: str = "") -> None:
        super().__init__()
        self._connect = connect
        self._client: Client | None = None
        self._bots: list[dict] = []
        self._bot: dict = {}
        self._overview: list[dict] = []
        self._library: list[dict] = []
        self._days: list[dict] = []
        self._day: dict = {}
        self._settings: dict = {}
        self._message = ""
        self._busy = 0
        self._wanted = bot or str(ui_settings.get(CHOSEN, ""))  # a bot's path or name to show first
        self._theme_name = theme_name
        self._colors = theme.colors(theme_name)
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

    bots = Property(list, _get_bots, notify=botsChanged)
    bot = Property(dict, _get_bot, notify=botChanged)
    overview = Property(list, _get_overview, notify=overviewChanged)
    library = Property(list, _get_library, notify=libraryChanged)
    days = Property(list, _get_days, notify=daysChanged)
    day = Property(dict, _get_day, notify=dayChanged)
    settings = Property(dict, _get_settings, notify=settingsChanged)
    message = Property(str, _get_message, notify=messageChanged)
    busy = Property(bool, _get_busy, notify=busyChanged)
    colors = Property(dict, _get_colors, notify=themeChanged)
    themeName = Property(str, _get_theme, notify=themeChanged)
    glass = Property(bool, _get_glass, notify=themeChanged)
    now = Property(float, _get_now, notify=clockChanged)

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
            self.captureWanted.emit(self._bot["path"], mode)

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
        self._theme_name = name if name in theme.THEMES else theme.DEFAULT
        self._colors = theme.colors(self._theme_name)
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
