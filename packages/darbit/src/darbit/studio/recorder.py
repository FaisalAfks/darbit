"""The recorder in darbit Studio: a floating pill while keys, clicks and the mouse go into an action.

The work is server/record_api.py's (every event on one clock, saved as a tape), in the input worker (worker.py), a
process of its own so the Studio can't delay an input; this hands it to QML. Clicks on the pill itself are left out
of the recording. While paused, a check can go in: a wait, or a picture to wait for or until it's gone, taken with
Capture.
"""

from pathlib import Path

from PySide6.QtCore import Property, QObject, Signal, Slot

from .. import keymap
from ..platform import hotkeys
from ..platform.backend import NotSupported
from .worker_link import WorkerGone, WorkerLink

KEYS = {"record.toggle": "finish", "record.mark": "mark", "run.pause": "pause"}  # global keys while recording


def _combo(action: str) -> str:
    """The keys an action has in the user's keymap, in whichever scope it's listed."""
    for scope in keymap.load().values():
        if action in scope:
            return str(scope[action])
    return ""


class Recorder(QObject):
    """One recording at a time, for QML."""

    stateChanged = Signal()
    finished = Signal(str)  # the action's name when kept, "" when cancelled
    pictureWanted = Signal(str, bool)  # (the bot's folder, until gone): a check to take with Capture

    _ticked = Signal(object)  # record.tick's status, from the recorder's thread
    _keyed = Signal(str)  # a global key, from the hotkeys' thread

    def __init__(self, link: WorkerLink | None = None) -> None:
        super().__init__()
        self._state: dict = {"recording": False}
        self._link = link or WorkerLink(self._from_worker)
        self._link.on_event = self._from_worker
        self._registered: object = None
        self._area = [0, 0, 0, 0]  # the pill on screen, sent to the worker once a recording starts
        self._ticked.connect(self._take)
        self._keyed.connect(self._key)

    def _get(self, key: str, default: object) -> object:
        return self._state.get(key, default)

    def _get_active(self) -> bool:
        return bool(self._state.get("recording"))

    def _get_paused(self) -> bool:
        return bool(self._state.get("paused"))

    def _get_seconds(self) -> float:
        return float(self._state.get("seconds", 0.0))

    def _get_count(self) -> int:
        return int(self._state.get("count", 0))

    def _get_checks(self) -> int:
        return int(self._state.get("checks", 0))

    def _get_parts(self) -> int:
        return int(self._state.get("parts", 1))

    def _get_steps(self) -> list:
        return list(self._state.get("steps", []))

    def _get_name(self) -> str:
        return str(self._state.get("name", ""))

    active = Property(bool, _get_active, notify=stateChanged)
    paused = Property(bool, _get_paused, notify=stateChanged)
    seconds = Property(float, _get_seconds, notify=stateChanged)
    count = Property(int, _get_count, notify=stateChanged)
    checks = Property(int, _get_checks, notify=stateChanged)
    parts = Property(int, _get_parts, notify=stateChanged)
    steps = Property(list, _get_steps, notify=stateChanged)
    name = Property(str, _get_name, notify=stateChanged)

    def start(self, folder: Path, name: str, replace: bool = False) -> str:
        """Start recording into the bot's actions/<name>.py; "" when it started, else why not."""
        try:
            self._take(self._link.call("record.start", path=str(folder), name=name, replace=replace))
        except (ValueError, WorkerGone) as error:
            return str(error)
        self._call("record.area", area=self._area)
        self._register_keys()
        return ""

    @Slot()
    def pause(self) -> None:
        self._call("record.pause")

    @Slot()
    def mark(self) -> None:
        """A checkpoint: what came before becomes its own action."""
        self._call("record.mark")

    @Slot(float)
    def addWait(self, seconds: float) -> None:
        self._call("record.check", kind="wait", seconds=seconds)

    @Slot(str, bool)
    def addPicture(self, name: str, gone: bool) -> None:
        """A check for a picture the bot has: wait for it, or until it's gone."""
        self._call("record.check", kind="picture", target=name, gone=gone)

    @Slot(bool)
    def takePicture(self, gone: bool) -> None:
        """Take a new picture for a check with Capture; it's added when it's saved."""
        folder = self._state.get("path")
        if folder:
            self.pictureWanted.emit(str(folder), gone)

    @Slot()
    def removeLast(self) -> None:
        self._call("record.remove_last")

    @Slot(bool)
    def finish(self, keep: bool) -> None:
        """Stop: save the action (`keep`) or throw the recording away."""
        if not self.active:
            return
        name = self.name
        self._unregister_keys()
        try:
            self._link.call("record.stop", keep=keep)
        except (ValueError, WorkerGone):
            pass
        self._state = {"recording": False}
        self.stateChanged.emit()
        self.finished.emit(name if keep else "")

    @Slot(int, int, int, int)
    def setArea(self, x: int, y: int, width: int, height: int) -> None:
        """Where the pill is on screen: clicks there aren't recorded."""
        self._area = [x, y, width, height]
        if self.active:
            self._call("record.area", area=[x, y, width, height])

    def _call(self, method: str, **params: object) -> None:
        try:
            self._take(self._link.call(method, **params))
        except (ValueError, WorkerGone):
            pass

    def _from_worker(self, topic: str, data: dict) -> None:
        if topic == "record.tick":
            self._ticked.emit(data)

    @Slot(object)
    def _take(self, state: object) -> None:
        if isinstance(state, dict) and state.get("recording"):
            self._state = state
            self.stateChanged.emit()

    def _register_keys(self) -> None:
        keys = {}
        handlers = {}
        for action, what in KEYS.items():
            keys[action] = _combo(action)
            handlers[action] = lambda what=what: self._keyed.emit(what)
        shortcuts = {}
        for action, combo in keys.items():
            if combo:
                shortcuts[action] = combo
        self._call("record.keys", keys=shortcuts)  # for the recorder's own status
        try:
            self._registered = hotkeys.register(shortcuts, handlers)
        except NotSupported:
            self._registered = None

    def _unregister_keys(self) -> None:
        registered = self._registered
        self._registered = None
        if registered is not None:
            registered.stop()

    @Slot(str)
    def _key(self, what: str) -> None:
        if what == "finish":
            self.finish(True)
        elif what == "mark":
            self.mark()
        elif what == "pause":
            self.pause()

    def close(self) -> None:
        self._link.close()
