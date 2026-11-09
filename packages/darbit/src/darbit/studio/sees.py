"""The Studio's end of "What the bot sees" (#316): while the block is in sight, it keeps the watching file fresh so
the shown bot keeps a picture of its looks (runtime/sees.py), and reads the bot's last look once a second for the block.

Out of sight (another page, the window hidden or minimized) it stops: the watching file goes, nothing is read, and the
block's picture doesn't change, so nothing is decoded either.
"""

import json
import time
from pathlib import Path

from PySide6.QtCore import Property, QCoreApplication, QObject, QTimer, Signal, Slot

from ..runtime import sees as bot_sees

READ_EVERY_MS = 1000  # how often the bot's last look is read
TELL_EVERY = 2.0  # seconds between writes of the watching file: well inside runtime/sees.py's FRESH


class Sees(QObject):
    changed = Signal()

    def __init__(self) -> None:
        super().__init__()
        self._look = ""  # the bot's look file (logs/sees.json) followed now; "" while the block is out of sight
        self._logs = ""
        self._stamp = 0.0  # the look file's modified time when last read
        self._told = 0.0
        self._frame: dict = {}
        self._timer = QTimer(self)
        self._timer.setInterval(READ_EVERY_MS)
        self._timer.timeout.connect(self._read)
        app = QCoreApplication.instance()
        if app is not None:
            app.aboutToQuit.connect(self.stop)

    def _get_frame(self) -> dict:
        return self._frame

    # the last look: {time, kind, targets, found, picture (a file URL), w, h, boxes: [{name, x, y, w, h, score, found}]}
    frame = Property(dict, _get_frame, notify=changed)

    @Slot(str, str)
    def follow(self, look: str, logs: str) -> None:
        """Follow a bot's look file (the block came into sight), or stop following with "" (it left)."""
        if not look:
            self.stop()
            return
        if look != self._look:
            self._look = look
            self._logs = logs
            self._stamp = 0.0
            self._frame = {}
            self.changed.emit()
        self._told = 0.0
        self._read()
        self._timer.start()

    @Slot()
    def stop(self) -> None:
        self._timer.stop()
        if not self._look:
            return
        self._look = ""
        try:
            bot_sees.watching_file().unlink(missing_ok=True)
        except OSError:
            pass

    def _read(self) -> None:
        self._tell()
        place = Path(self._look)
        try:
            stamp = place.stat().st_mtime
        except OSError:
            return
        if stamp == self._stamp:
            return
        try:
            look = json.loads(place.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return  # half written on another system: the next read gets it
        if not isinstance(look, dict) or not look.get("picture"):
            return
        self._stamp = stamp
        picture = place.with_name(str(look["picture"]))
        # a new address for each picture: the block's Image loads it again instead of keeping the one it had
        self._frame = {**look, "picture": f"{picture.as_uri()}?{stamp}"}
        self.changed.emit()

    def _tell(self) -> None:
        """Keep the watching file fresh, naming the bot's logs folder."""
        if time.time() - self._told < TELL_EVERY:
            return
        self._told = time.time()
        place = bot_sees.watching_file()
        try:
            place.parent.mkdir(parents=True, exist_ok=True)
            place.write_text(json.dumps({"logs": self._logs}), encoding="utf-8")
        except OSError:
            pass
