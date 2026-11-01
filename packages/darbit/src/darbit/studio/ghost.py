"""The ghost cursor's listening end (#117): the clicks and keys bots tell (platform/ghost.py), kept for a moment so
GhostWindow.qml can show them over the game.

The Studio listens on a free local UDP port and writes it in the ghost file; it removes the file when it stops.
A mark lasts SHOWN seconds. While there are none, nothing runs: no timer, and the window is hidden.
"""

import json
import time

from PySide6.QtCore import Property, QObject, QTimer, Signal, Slot
from PySide6.QtNetwork import QHostAddress, QUdpSocket

from ..platform import ghost as told

SHOWN = 0.9  # seconds a click or key stays on screen
MOST = 12  # marks shown at once: a burst of keys shows its last ones
PRUNE_MS = 100


class Ghost(QObject):
    changed = Signal()

    def __init__(self) -> None:
        super().__init__()
        self._socket: QUdpSocket | None = None
        self._marks: list[dict] = []
        self._next = 0
        self._timer = QTimer(self)
        self._timer.setInterval(PRUNE_MS)
        self._timer.timeout.connect(self._prune)

    def _get_marks(self) -> list:
        return self._marks

    def _get_on(self) -> bool:
        return self._socket is not None

    marks = Property(list, _get_marks, notify=changed)  # {id, kind, x, y, name, age}: newest last
    isOn = Property(bool, _get_on, notify=changed)

    @Slot()
    def start(self) -> None:
        """Listen, and tell bots where (the ghost file)."""
        if self._socket is not None:
            return
        listener = QUdpSocket(self)
        if not listener.bind(QHostAddress.SpecialAddress.LocalHost, 0):
            return
        listener.readyRead.connect(self._read)
        self._socket = listener
        place = told.path()
        try:
            place.parent.mkdir(parents=True, exist_ok=True)
            place.write_text(json.dumps({"port": listener.localPort()}), encoding="utf-8")
        except OSError:
            pass
        self.changed.emit()

    @Slot()
    def stop(self) -> None:
        if self._socket is None:
            return
        self._socket.close()
        self._socket = None
        try:
            told.path().unlink(missing_ok=True)
        except OSError:
            pass
        self._marks = []
        self._timer.stop()
        self.changed.emit()

    def take(self, data: dict) -> None:
        """One click or key a bot told."""
        kind = data.get("kind")
        if kind not in ("click", "key"):
            return
        try:
            mark = {"id": self._next, "kind": kind, "x": int(data.get("x", 0)), "y": int(data.get("y", 0))}
        except (TypeError, ValueError):
            return
        mark["name"] = str(data.get("name", data.get("button", "")))[:24]
        mark["at"] = time.monotonic()
        self._next += 1
        self._marks = (self._marks + [mark])[-MOST:]
        if not self._timer.isActive():
            self._timer.start()
        self.changed.emit()

    def _read(self) -> None:
        while self._socket is not None and self._socket.hasPendingDatagrams():
            datagram = self._socket.receiveDatagram()
            try:
                data = json.loads(bytes(datagram.data()).decode("utf-8"))
            except (ValueError, UnicodeDecodeError):
                continue
            if isinstance(data, dict):
                self.take(data)

    def _prune(self) -> None:
        now = time.monotonic()
        kept = [mark for mark in self._marks if now - mark["at"] < SHOWN]
        if len(kept) != len(self._marks):
            self._marks = kept
            self.changed.emit()
        if not kept:
            self._timer.stop()
