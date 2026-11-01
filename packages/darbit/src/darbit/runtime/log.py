"""One log file per day, a run report alongside it, and screenshots when a long wait runs out.

The log (logs/<day>.log) is for reading. The run report (logs/report-<day>.jsonl) has
one JSON line per event (searches, clicks, steps) for tools to summarise:
python -m darbit.tools.report.
"""

import json
import logging
import threading
import time
from datetime import datetime
from pathlib import Path

import cv2

from ..events import listen, publish
from ..platform import screen
from ..settings import settings

logger = logging.getLogger("darbit")
_day = ""
_KEEP_SHOTS = 200


def _handler() -> None:
    global _day
    today = datetime.now().strftime("%Y-%m-%d")
    if today == _day:
        return
    for old in list(logger.handlers):
        if getattr(old, "_darbit", False):
            logger.removeHandler(old)
            old.close()
    settings.logs.mkdir(parents=True, exist_ok=True)
    handler = logging.FileHandler(settings.logs / f"{today}.log", encoding="utf-8")
    handler.setFormatter(logging.Formatter("%(asctime)s %(message)s", "%H:%M:%S"))
    handler._darbit = True  # type: ignore[attr-defined]
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    _day = today


def log(message: str) -> None:
    """Write a line to today's log file, and send it to any open darbit window."""
    publish("log", {"line": message, "time": datetime.now().strftime("%H:%M:%S")})
    if not settings.log:
        return
    try:
        _handler()
        logger.info(message)
    except OSError:
        pass


_report_lock = threading.Lock()


def record(event: str, **fields: object) -> None:
    """Add an event to today's run report, and send it to any open darbit window."""
    line = {"time": datetime.now().isoformat(timespec="milliseconds"), "event": event, **fields}
    publish("record", {"event": event, "fields": line})
    if not settings.log:
        return
    try:
        settings.logs.mkdir(parents=True, exist_ok=True)
        with _report_lock, (settings.logs / f"report-{datetime.now():%Y-%m-%d}.jsonl").open("a", encoding="utf-8") as f:
            f.write(json.dumps(line, default=str) + "\n")
    except OSError:
        pass


def screenshot(label: str) -> str | None:
    """Save the screen into logs/screenshots, keeping the newest few hundred. Returns the file's name."""
    if not settings.log:
        return None
    try:
        folder = settings.logs / "screenshots"
        folder.mkdir(parents=True, exist_ok=True)
        pixels, _ = screen.grab()
        safe = "".join(c if c.isalnum() or c in "-_." else "_" for c in label)[:60]
        path = folder / f"{datetime.now():%Y-%m-%d_%H-%M-%S}_{safe}.jpg"
        ok, data = cv2.imencode(".jpg", pixels, [cv2.IMWRITE_JPEG_QUALITY, 85])  # about 10x smaller than PNG
        if ok:
            data.tofile(str(path))
            log(f"screenshot {path.name}")
        shots = [*folder.glob("*.png"), *folder.glob("*.jpg")]  # older ones were PNG
        shots.sort(key=_modified_time)
        for old in shots[:-_KEEP_SHOTS]:
            old.unlink(missing_ok=True)
        return path.name if ok else None
    except OSError:
        return None


def since(started: float) -> str:
    return f"{time.monotonic() - started:.1f}s"


def _modified_time(path: Path) -> float:
    return path.stat().st_mtime


def _on_event(topic: str, data: dict) -> None:
    """What the platform layer tells that belongs in the log and the run report."""
    if topic != "screen.locked":
        return
    if data.get("locked"):
        log("the screen is locked: waiting until it's back")
        record("screen", state="locked")
    else:
        log("the screen is back: going on")
        record("screen", state="back")


listen(_on_event)
