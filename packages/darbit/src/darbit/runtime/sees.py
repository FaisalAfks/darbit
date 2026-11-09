"""What the bot sees (#316): while darbit Studio shows its "What the bot sees" block, a look at the screen is kept as a
small JPEG of the app window with what it looked for boxed, at most once a second, in the bot's logs folder.

The Studio says it's watching by keeping data_dir/watching.json fresh, naming the logs folder of the bot it shows.
The bot reads that file at most once a second, so a look while nobody watches costs a clock read and nothing more.
A picture is made on a thread of its own, so a look never waits for it.
"""

import json
import os
import threading
import time
from datetime import datetime
from pathlib import Path

import cv2
import numpy as np

from .. import paths
from ..core.geometry import Region
from ..core.targets import Match, Target
from ..platform import screen, windows
from ..settings import settings
from .log import log

WATCHING = "watching.json"  # in data_dir: written by the Studio while the block is in sight
LOOK = "sees.json"  # in the bot's logs folder: the last look, naming its picture
FRESH = 5.0  # seconds a watching file stays good without being written again (a Studio that ended stops it)
CHECK_EVERY = 1.0  # seconds between reads of the watching file
FRAME_EVERY = 1.0  # seconds between pictures
CHANGED_EVERY = 0.25  # seconds between pictures when a look finds something the last picture didn't
WIDTH = 640  # the picture's width at most, in pixels
QUALITY = 70  # JPEG quality: about 30 KB for a 640 px picture

_lock = threading.Condition()
_checked = [-CHECK_EVERY]
_watched = [False]
_last = {"at": -FRAME_EVERY, "found": None, "slot": 0}
_waiting: list[tuple] = []  # the look to make a picture of, at most one: a newer one takes its place
_busy = [False]  # the picture thread is making one
_thread: list[threading.Thread | None] = [None]
_said: set[str] = set()  # why pictures couldn't be made, each logged once


def watching_file() -> Path:
    return paths.data_dir() / WATCHING


def watched() -> bool:
    """Whether the Studio shows this bot's "What the bot sees" now (as of the last read, at most a second ago)."""
    now = time.monotonic()
    if now - _checked[0] >= CHECK_EVERY:
        _checked[0] = now
        _watched[0] = _read_watching()
    return _watched[0]


def _read_watching() -> bool:
    try:
        place = watching_file()
        if time.time() - place.stat().st_mtime > FRESH:
            return False
        logs = json.loads(place.read_text(encoding="utf-8"))["logs"]
    except (OSError, ValueError, KeyError, TypeError):
        return False
    return _same_folder(Path(str(logs)), settings.logs)


def _same_folder(one: Path, other: Path) -> bool:
    return os.path.normcase(os.path.abspath(one)) == os.path.normcase(os.path.abspath(other))


def look(
    kind: str, chosen: list[Target], tried: list[Match], found: Match | None, pixels: np.ndarray, origin: Region
) -> None:
    """Keep this look as the picture of what the bot sees, if the Studio is watching and one is due. Never raises,
    and never waits: the picture is made on its own thread (the look's pixels aren't changed after it, so they're
    handed over as they are). `chosen` is what was looked for, `tried` the best spot of each target searched."""
    if not kind or not watched():
        return
    found_name = found.name if found is not None else None
    with _lock:
        since = time.monotonic() - _last["at"]
        wait = CHANGED_EVERY if found_name != _last["found"] else FRAME_EVERY
        if since < wait:
            return
        _last["at"] = time.monotonic()
        _last["found"] = found_name
        _last["slot"] = 1 - _last["slot"]
        _waiting[:] = [(kind, list(chosen), list(tried), found, pixels, origin, _last["slot"])]
        if _thread[0] is None or not _thread[0].is_alive():
            _thread[0] = threading.Thread(target=_make_pictures, name="darbit-sees", daemon=True)
            _thread[0].start()
        _lock.notify_all()


def _make_pictures() -> None:
    while True:
        with _lock:
            while not _waiting:
                _lock.wait()
            one = _waiting.pop()
            _busy[0] = True
        try:
            _write(*one)
        except Exception as error:  # noqa: BLE001 - a picture that can't be made is skipped; the bot goes on
            _say_once(f"What the bot sees: no picture ({error})")
        finally:
            with _lock:
                _busy[0] = False
                _lock.notify_all()


def _say_once(message: str) -> None:
    if message not in _said:
        _said.add(message)
        log(message)


def settled(timeout: float = 5.0) -> bool:
    """Wait until the picture asked for last is written (for tests and probes)."""
    with _lock:
        return _lock.wait_for(lambda: not _waiting and not _busy[0], timeout)


def _write(
    kind: str,
    chosen: list[Target],
    tried: list[Match],
    found: Match | None,
    pixels: np.ndarray,
    origin: Region,
    slot: int,
) -> None:
    area = _frame_area(origin)
    frame = _pixels_of(area, pixels, origin)
    if frame.size == 0:
        return
    height, width = frame.shape[:2]
    shrink = min(1.0, WIDTH / width)
    if shrink < 1:
        frame = cv2.resize(frame, (round(width * shrink), round(height * shrink)), interpolation=cv2.INTER_AREA)
    ok, data = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, QUALITY])
    if not ok:
        return
    folder = settings.logs
    folder.mkdir(parents=True, exist_ok=True)
    picture = f"sees-{slot}.jpg"  # two in turn: the one the Studio is showing is never written over
    _replace(folder / picture, data.tobytes())
    boxes = []
    for match in tried:
        box = _box_of(match, area, shrink, found)
        if box is not None:
            boxes.append(box)
    names = []
    for one in chosen:
        if one.label not in names:
            names.append(one.label)
    look_line = {
        "time": datetime.now().isoformat(timespec="milliseconds"),
        "kind": kind,
        "targets": names,
        "found": found.name if found is not None else None,
        "picture": picture,
        "w": frame.shape[1],
        "h": frame.shape[0],
        "boxes": boxes,
    }
    _replace(folder / LOOK, json.dumps(look_line).encode("utf-8"))


def _frame_area(origin: Region) -> Region:
    """What the picture shows: the app window, else the monitor the look was on."""
    if settings.window:
        found = windows.matching(settings.window, loose=True)
        if found:
            window = windows.region(found[0].handle)
            if window.w > 0 and window.h > 0:
                return window
    middle = origin.center
    for monitor in screen.monitors():
        if monitor.contains(middle):
            return monitor
    return screen.desktop()


def _pixels_of(area: Region, pixels: np.ndarray, origin: Region) -> np.ndarray:
    """The area's pixels: cut from the look's own when it holds the whole area, else grabbed once more."""
    inside = area.intersect(origin)
    if inside is not None and inside == area:
        x, y = area.x - origin.x, area.y - origin.y
        return pixels[y : y + area.h, x : x + area.w]
    grabbed, _ = screen.grab(area)
    return grabbed


def _box_of(match: Match, area: Region, shrink: float, found: Match | None) -> dict | None:
    """A box on the picture, in its pixels: found, or the closest spot of a target that wasn't."""
    if match.region.intersect(area) is None:
        return None
    return {
        "name": match.name or match.target.label,
        "x": round((match.x - area.x) * shrink),
        "y": round((match.y - area.y) * shrink),
        "w": max(1, round(match.w * shrink)),
        "h": max(1, round(match.h * shrink)),
        "score": round(match.score, 3),
        "found": found is not None and match is found,
    }


def _replace(path: Path, data: bytes) -> None:
    """Write a file whole: a reader sees the old one or the new one, never half of one."""
    part = path.with_name(path.name + ".part")
    part.write_bytes(data)
    os.replace(part, path)


def forget() -> None:
    """Read the watching file again at the next look, and make the next picture (for tests)."""
    settled()
    _checked[0] = -CHECK_EVERY
    _last["at"] = -FRAME_EVERY
    _last["found"] = None
