"""One log file per day, a run report alongside it, and screenshots when a long wait runs out.

The log (logs/<day>.log) is for reading. The run report (logs/report-<day>.jsonl) has
one JSON line per event (searches, clicks, steps) for tools to summarise:
python -m darbit.tools.report. Both are kept for `settings.keep_days` days (decision 0021).
"""

import json
import logging
import threading
import time
from datetime import datetime
from pathlib import Path

import cv2

from .. import days
from ..events import listen, publish
from ..platform import screen
from ..settings import settings

logger = logging.getLogger("darbit")
_day = ""
_tidied: tuple[Path, str] | None = None  # the folder and day old logs and reports were last deleted for
_KEEP_SHOTS = 200
REPORT_PREFIX = "report-"
REPORT_SUFFIX = ".jsonl"
_waiting: list[str] = []  # lines kept by `later` until the run writes something of its own
_waiting_lock = threading.Lock()


def _today() -> str:
    """The bot's day now: its log and report files are named by it, so a day that starts at 03:00 stays one file."""
    return days.today(days.of({"day_starts": settings.day_starts}))


def _handler() -> None:
    global _day
    today = _today()
    if today == _day:
        return
    _forget_old(today)
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


def later(message: str) -> None:
    """Keep a line for the log until the next line or report event: a script that only reads a bot (its tests,
    `darbit status`) writes nothing to the bot's log, a running bot gets the line first."""
    with _waiting_lock:
        _waiting.append(message)


def forget_later() -> None:
    """Drop the lines `later` kept and nothing wrote yet: a process that sets a bot up again starts with its own."""
    with _waiting_lock:
        _waiting.clear()


def _write_waiting() -> None:
    if not _waiting:
        return
    with _waiting_lock:  # observer threads log too: each kept line is written once
        lines = list(_waiting)
        _waiting.clear()
    for line in lines:
        _write(line)


def log(message: str) -> None:
    """Write a line to today's log file, and send it to any open darbit window."""
    _write_waiting()
    _write(message)


def _write(message: str) -> None:
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
    _write_waiting()
    line = {"time": datetime.now().isoformat(timespec="milliseconds"), "event": event, **fields}
    publish("record", {"event": event, "fields": line})
    if not settings.log:
        return
    try:
        today = _today()
        _forget_old(today)
        settings.logs.mkdir(parents=True, exist_ok=True)
        with _report_lock, (settings.logs / f"{REPORT_PREFIX}{today}{REPORT_SUFFIX}").open("a", encoding="utf-8") as f:
            f.write(json.dumps(line, default=str) + "\n")
    except OSError:
        pass


def _forget_old(today: str) -> None:
    """Delete the logs and reports older than keep_days, once a day: when the bot starts writing, and each new day."""
    global _tidied
    if _tidied == (settings.logs, today):
        return
    _tidied = (settings.logs, today)
    forget_files_before(settings.logs, days.first_kept(today, settings.keep_days))


def forget_files_before(folder: Path, day: str) -> int:
    """Delete the run reports and daily logs in `folder` from before `day` ("2026-10-26"); how many went."""
    if not folder.is_dir():
        return 0
    gone = 0
    for path in [*folder.glob(f"{REPORT_PREFIX}*{REPORT_SUFFIX}"), *folder.glob("????-??-??.log")]:
        if day_of_file(path) >= day:
            continue
        try:
            path.unlink()
            gone += 1
        except OSError:
            continue  # open on Windows (a reader has it): next time
    return gone


def day_of_file(path: Path) -> str:
    """The day a run report or daily log is for: "2026-10-26" from report-2026-10-26.jsonl or 2026-10-26.log."""
    if path.name.startswith(REPORT_PREFIX) and path.name.endswith(REPORT_SUFFIX):
        return path.name[len(REPORT_PREFIX) : -len(REPORT_SUFFIX)]
    return path.stem


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
