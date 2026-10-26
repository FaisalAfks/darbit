"""The web capture tool's work, without any UI: one capture session at a time (decision 0013, round 7).

    start(project_folder, images, items)   # what to take: the guide's missing pictures, one asset, or anything
    freeze()                               # grab the screen once; everything after works on this shot
    candidates(x, y, "image")              # boxes around a click, smallest first
    test(box, region, similarity)          # every place the boxed picture is found in its region, with scores
    save(name, kind, image, region, point) # write the target's files, like the old capture tool

Coordinates are pixels of the frozen shot. server/capture_api.py turns these into requests; nothing here imports
the server. See docs/tasks/T09-capture-overlay.md.
"""

import time
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

from ..core.geometry import Location, Region
from ..core.matching import every
from ..core.targets import Target, read_image
from ..platform import screen
from .common import Item, Result, captured
from .engine import Prepared, pick, prepare
from .engine import candidates as engine_candidates
from .store import save_result

LOOK_ALIKE = 0.5  # Test shows matches down to this score, so look-alikes under the line show too
MOST_MATCHES = 12
KINDS = {"image": "image", "region": "region", "point": "location", "location": "location"}


class CaptureError(ValueError):
    """Something the capture session can't do; the message says why."""


@dataclass
class Session:
    project: Path
    images: Path  # where targets are saved
    items: list[Item] = field(default_factory=list)  # still to take, in order
    shot: np.ndarray | None = None
    origin: Region | None = None
    prepared: Prepared | None = None


_session: Session | None = None


def start(project: Path, images: Path, items: list[Item]) -> dict:
    """Begin a capture session for a bot. Items already taken are left out."""
    global _session
    waiting = []
    for item in items:
        if not captured(item, images):
            waiting.append(item)
    _session = Session(project, images, waiting)
    return {"items": describe(waiting)}


def describe(items: list[Item]) -> list[dict]:
    found = []
    for item in items:
        kind = item.kind
        if kind == "location":
            kind = "point"
        found.append({"name": item.name, "kind": kind, "say": item.note, "screen": item.screen})
    return found


def _current() -> Session:
    if _session is None:
        raise CaptureError("no capture session; open Capture from the Studio")
    return _session


def freeze() -> tuple[np.ndarray, Region]:
    """Grab the main screen once and work out its edges. Returns the shot and where it sits on the desktop."""
    session = _current()
    area = screen.monitors()[0]
    shot, origin = screen.grab(area)
    session.shot = shot
    session.origin = origin
    session.prepared = prepare(shot)
    return shot, origin


def _frozen() -> tuple[Session, np.ndarray, Region, Prepared]:
    session = _current()
    if session.shot is None or session.origin is None or session.prepared is None:
        raise CaptureError("nothing frozen yet")
    return session, session.shot, session.origin, session.prepared


def candidates(x: int, y: int, kind: str) -> dict:
    """Boxes around a click on the shot, smallest first, and which one a click starts with."""
    _, _, _, prepared = _frozen()
    engine_kind = "region" if kind == "region" else "image"
    boxes = engine_candidates(prepared, x, y, engine_kind)
    found = []
    for box in boxes:
        found.append([box.x, box.y, box.w, box.h])
    return {"boxes": found, "start": pick(boxes)}


def _inside(box: list[int], shot: np.ndarray) -> Region:
    height, width = shot.shape[:2]
    x = max(0, min(int(box[0]), width - 1))
    y = max(0, min(int(box[1]), height - 1))
    w = max(1, min(int(box[2]), width - x))
    h = max(1, min(int(box[3]), height - y))
    return Region(x, y, w, h)


def test(box: list[int] | None, name: str | None, region: list[int] | None, similarity: float) -> dict:
    """Every place a picture is found in its region of the shot, best first, down to look-alikes.

    The picture is the boxed part of the shot, or a saved target by name."""
    session, shot, _, _ = _frozen()
    started = time.perf_counter()
    if box is not None:
        part = _inside(box, shot)
        pixels = shot[part.y : part.bottom, part.x : part.right].copy()
    elif name:
        path = session.images / (name + ".png")
        if not path.is_file():
            raise CaptureError(f"no picture called {name}")
        pixels = read_image(path)
    else:
        raise CaptureError("box something first")
    area = Region(0, 0, shot.shape[1], shot.shape[0])
    if region is not None:
        area = _inside(region, shot)
    haystack = shot[area.y : area.bottom, area.x : area.right]
    target = Target(name=name or "the box", _pixels=pixels)
    matches = every(target, haystack, area, LOOK_ALIKE, MOST_MATCHES)
    found = []
    for match in matches:
        found.append({"x": match.x, "y": match.y, "w": match.w, "h": match.h, "score": round(match.score, 3)})
    milliseconds = round((time.perf_counter() - started) * 1000)
    return {
        "matches": found,
        "similarity": similarity,
        "ms": milliseconds,
        "searched": [area.x, area.y, area.w, area.h],
    }


def save(name: str, kind: str, image: list[int] | None, region: list[int] | None, point: list[float] | None) -> dict:
    """Write a target's files from the frozen shot, then move on to the next item."""
    session, shot, origin, _ = _frozen()
    if not name:
        raise CaptureError("give it a name")
    capture_kind = KINDS.get(kind)
    if capture_kind is None:
        raise CaptureError(f"no kind called {kind}")
    result = Result()
    if region is not None:
        part = _inside(region, shot)
        result.region = Region(part.x + origin.x, part.y + origin.y, part.w, part.h)
    if point is not None:
        result.point = Location(point[0] + origin.x, point[1] + origin.y)
    if capture_kind == "image":
        if image is None:
            raise CaptureError("box the picture first")
        part = _inside(image, shot)
        result.image = Region(part.x + origin.x, part.y + origin.y, part.w, part.h)
    elif capture_kind == "region" and result.region is None and image is not None:
        part = _inside(image, shot)
        result.region = Region(part.x + origin.x, part.y + origin.y, part.w, part.h)
    elif capture_kind == "location" and result.point is None:
        raise CaptureError("click the point first")
    item = Item(name, capture_kind)
    saved = save_result(session.images, item, result, shot, origin, None)
    remaining = []
    for waiting in session.items:
        if waiting.name != name:
            remaining.append(waiting)
    session.items = remaining
    return {"message": saved.message, "risky": saved.risky, "items": describe(remaining)}


def stop() -> None:
    """End the session and let go of the shot."""
    global _session
    _session = None
