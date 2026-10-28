"""Input tapes (decision 0014): everything the keyboard and mouse did while recording, played back on one clock.

    d.replay(__file__, 0.0, 42.5)   # in actions/dim_run.py: plays actions/dim_run.tape.json from 0 s to 42.5 s

A tape keeps every mouse packet with both what the mouse sent (counts) and where the cursor was, every key and
button going down and up, and the wheel. Playing it sends each one at the time it happened. For a packet the game
held the cursor for (a camera: Roblox's shift lock, a right-drag) it sends the same counts, which turn the camera the
same; otherwise it puts the cursor where it was, which is exact whatever the Windows mouse settings are. Places are
kept relative to settings.window, so a moved or resized game window still lines up.
"""

import json
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path

from ..errors import Stopped
from ..platform import input as device
from ..platform import safety, windows
from ..settings import settings
from . import actions

VERSION = 1
SUFFIX = ".tape.json"
HOLD_BUCKET = 0.03  # seconds of mouse packets looked at together to tell a held cursor from a free one
HOLD_COUNTS = 4  # counts the mouse must move in a bucket to tell; less, and the bucket is like the one before
HOLD_PACKETS = 3  # packets a bucket needs for that; fewer, and it's like the one before
SNAP_BACK = 3  # px the cursor jumping against the mouse's way that means the game put it back
FOLLOW_SHARE = 0.25  # a free cursor goes at least this share of the counts, even at a slow pointer speed
SLEEP_AHEAD = 0.0015  # seconds before an event when sleeping stops and waiting goes on in a tight loop
SUMMARY_POINTS = 240  # cursor places sent to the Studio for a tape's mini path
SUMMARY_MARKS = 240

stopping = threading.Event()  # set by darbit Studio's Stop: a replay ends at its next event


@dataclass
class Event:
    """One thing that happened, `t` seconds into the recording."""

    t: float
    kind: str  # "move", "key", "button", "wheel", "hwheel"
    name: str = ""  # the key or the button (left, right, middle)
    up: bool = False  # a key or button going up
    dx: int = 0  # move: counts the mouse sent; wheel: notches, up (or right) positive
    dy: int = 0
    x: int = 0  # where the cursor was
    y: int = 0
    shown: bool = True  # move: the cursor was showing
    held: bool = False  # move: the game held the cursor, so the counts are what it read


@dataclass
class Tape:
    events: list[Event] = field(default_factory=list)
    window: list[int] | None = None  # the game window's client area when recorded: x, y, width, height
    screen: list[int] | None = None  # the whole desktop when recorded: x, y, width, height


# ---- reading and writing


def path_for(action_file: str | Path) -> Path:
    """actions/dim_run.py keeps its tape in actions/dim_run.tape.json."""
    path = Path(action_file)
    return path.with_name(path.stem + SUFFIX)


def save(path: Path, tape: Tape) -> None:
    rows = []
    for event in tape.events:
        rows.append(
            [
                round(event.t, 4),
                event.kind,
                event.name,
                int(event.up),
                event.dx,
                event.dy,
                event.x,
                event.y,
                int(event.shown),
                int(event.held),
            ]
        )
    data = {"version": VERSION, "window": tape.window, "screen": tape.screen, "events": rows}
    path.write_text(json.dumps(data, separators=(",", ":")), encoding="utf-8")


def load(path: Path) -> Tape:
    data = json.loads(path.read_text(encoding="utf-8"))
    events = []
    for row in data.get("events", []):
        t, kind, name, up, dx, dy, x, y, shown, held = row
        events.append(Event(t, kind, name, bool(up), dx, dy, x, y, bool(shown), bool(held)))
    return Tape(events, data.get("window"), data.get("screen"))


# ---- telling a held cursor from a free one


def mark_held(events: list[Event], screen: list[int] | None = None) -> None:
    """Set `held` on every move: the game held the cursor (a camera) rather than letting it follow the mouse.

    A free cursor always moves the way the mouse moved. One a game holds is hidden, or stays put, or jumps back
    against the movement each time the game puts it back. Moves are judged in short buckets; a bucket that can't
    tell (the mouse barely moved) is like the one before it. A cursor pushed against the edge of the screen
    (`screen`: x, y, width, height) is free.
    """
    bucket: list[Event] = []
    held = False
    previous: Event | None = None
    for event in events:
        if event.kind != "move":
            continue
        if bucket and event.t - bucket[0].t >= HOLD_BUCKET:
            held = _bucket_held(bucket, previous, held, screen)
            previous = bucket[-1]
            bucket = []
        bucket.append(event)
    if bucket:
        _bucket_held(bucket, previous, held, screen)


def _at_edge(x: int, y: int, screen: list[int] | None) -> bool:
    if not screen:
        return False
    left, top, width, height = screen
    return x <= left or y <= top or x >= left + width - 1 or y >= top + height - 1


def _bucket_held(bucket: list[Event], previous: Event | None, before: bool, screen: list[int] | None) -> bool:
    held = before
    if previous is None:
        previous = bucket[0]
    moved_x = 0
    moved_y = 0
    hidden = False
    snapped_back = False
    last = previous
    for event in bucket:
        moved_x += event.dx
        moved_y += event.dy
        hidden = hidden or not event.shown
        snapped_back = snapped_back or _snapped_back(event, last)
        last = event
    went_x = bucket[-1].x - previous.x
    went_y = bucket[-1].y - previous.y
    if hidden or snapped_back:
        held = True
    elif _at_edge(bucket[-1].x, bucket[-1].y, screen):
        held = False
    elif len(bucket) >= HOLD_PACKETS and (abs(moved_x) >= HOLD_COUNTS or abs(moved_y) >= HOLD_COUNTS):
        if abs(moved_x) >= abs(moved_y):
            held = not _followed(moved_x, went_x)
        else:
            held = not _followed(moved_y, went_y)
    for event in bucket:
        event.held = held
    return held


def _followed(moved: int, went: int) -> bool:
    """The cursor went the mouse's way, and about as far (Windows' pointer speed and acceleration aside)."""
    same_way = (moved > 0 and went > 0) or (moved < 0 and went < 0)
    return same_way and abs(went) >= abs(moved) * FOLLOW_SHARE


def _snapped_back(event: Event, before: Event) -> bool:
    """The cursor jumped against the way the mouse moved: the game put it back."""
    went_x = event.x - before.x
    went_y = event.y - before.y
    against_x = (event.dx >= 0 and went_x <= -SNAP_BACK) or (event.dx <= 0 and went_x >= SNAP_BACK)
    against_y = (event.dy >= 0 and went_y <= -SNAP_BACK) or (event.dy <= 0 and went_y >= SNAP_BACK)
    return against_x or against_y


# ---- playing


def replay(action_file: str | Path, start: float = 0.0, end: float | None = None) -> None:
    """Play the action's tape from `start` to `end` seconds, every event at its time."""
    tape = load(path_for(action_file))
    chosen = []
    for event in tape.events:
        if event.t < start:
            continue
        if end is not None and event.t >= end:
            break
        chosen.append(event)
    actions._front()
    place = Placing(tape.window, _window_now())
    began = time.perf_counter()
    for event in chosen:
        _wait_until(began + event.t - start)
        _send(event, place)
    if end is not None:
        _wait_until(began + end - start)  # the next step starts when it did while recording
    actions.resync()


class Placing:
    """Where a recorded place is now: the same spot in the game window, wherever the window is and however big."""

    def __init__(self, recorded: list[int] | None, now: list[int] | None) -> None:
        self.recorded = recorded
        self.now = now
        self.last: tuple[int, int] | None = None  # the last place the cursor was put
        self.held = False  # the last move was one the game held

    def spot(self, x: int, y: int) -> tuple[int, int]:
        if not self.recorded or not self.now:
            return x, y
        old_x, old_y, old_width, old_height = self.recorded
        new_x, new_y, new_width, new_height = self.now
        if old_width <= 0 or old_height <= 0:
            return x, y
        return (
            round(new_x + (x - old_x) * new_width / old_width),
            round(new_y + (y - old_y) * new_height / old_height),
        )

    def put(self, x: int, y: int) -> None:
        spot = self.spot(x, y)
        if spot != self.last:
            device.place(*spot)
            self.last = spot


def _send(event: Event, place: Placing) -> None:
    if event.kind == "move":
        place.held = event.held
        if event.held:
            device.nudge(event.dx, event.dy)
            place.last = None  # the game moves the cursor back; don't trust where it is
        else:
            place.put(event.x, event.y)
    elif event.kind == "key":
        device.key_now(event.name, event.up)
    elif event.kind == "button":
        if not place.held:
            place.put(event.x, event.y)
        device.button_now(event.name, event.up)
    elif event.kind == "wheel":
        device.wheel_now(event.dx)
    elif event.kind == "hwheel":
        device.wheel_now(event.dx, sideways=True)


def _wait_until(due: float) -> None:
    """Wait until `due` (perf_counter), sleeping most of it and waiting the last moment in a tight loop."""
    while True:
        safety.check()
        if stopping.is_set():
            raise Stopped("stopped from darbit Studio")
        left = due - time.perf_counter()
        if left <= 0:
            return
        if left > SLEEP_AHEAD:
            time.sleep(min(left - SLEEP_AHEAD, 0.05))
        else:
            time.sleep(0)


def _window_now() -> list[int] | None:
    if not settings.window:
        return None
    found = windows.matching(settings.window)
    if not found:
        return None
    area = windows.region(found[0].handle)
    return [area.x, area.y, area.w, area.h]


# ---- what the Studio shows for a tape


def summary(tape: Tape, start: float = 0.0, end: float | None = None) -> dict:
    """Counts, a thinned-out cursor path (0 to 1 across the window or desktop) and marks for keys, clicks and the
    wheel, for the editor's tape block."""
    chosen = []
    for event in tape.events:
        if event.t >= start and (end is None or event.t < end):
            chosen.append(event)
    area = tape.window or tape.screen or [0, 0, 1, 1]
    moves = 0
    held = 0
    keys = 0
    clicks = 0
    scrolls = 0
    places = []
    marks = []
    for event in chosen:
        if event.kind == "move":
            moves += 1
            if event.held:
                held += 1
            else:
                places.append([_share(event.x, area[0], area[2]), _share(event.y, area[1], area[3])])
        elif event.kind == "key" and not event.up:
            keys += 1
            marks.append({"t": round(event.t - start, 3), "kind": "key", "text": event.name})
        elif event.kind == "button" and not event.up:
            clicks += 1
            marks.append({"t": round(event.t - start, 3), "kind": "click", "text": event.name})
        elif event.kind in ("wheel", "hwheel"):
            scrolls += 1
            marks.append({"t": round(event.t - start, 3), "kind": "wheel", "text": str(event.dx)})
    seconds = 0.0
    if end is not None:
        seconds = end - start
    elif chosen:
        seconds = chosen[-1].t - start
    return {
        "seconds": round(seconds, 2),
        "moves": moves,
        "held": held,
        "keys": keys,
        "clicks": clicks,
        "scrolls": scrolls,
        "path": _thin(places, SUMMARY_POINTS),
        "marks": _thin(marks, SUMMARY_MARKS),
    }


def _share(value: int, origin: int, size: int) -> float:
    if size <= 0:
        return 0.0
    return round(min(max((value - origin) / size, 0.0), 1.0), 4)


def _thin(items: list, most: int) -> list:
    if len(items) <= most:
        return items
    kept = []
    step = len(items) / most
    at = 0.0
    while int(at) < len(items) and len(kept) < most:
        kept.append(items[int(at)])
        at += step
    return kept
