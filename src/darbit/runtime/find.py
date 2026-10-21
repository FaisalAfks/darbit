"""Looking for targets on screen. Not finding something returns None or False, never an error."""
from __future__ import annotations

import time
from pathlib import Path

from ..core import matching
from ..core.geometry import Region
from ..core.targets import Match, Target, find_file, load
from ..errors import TargetError
from ..platform import safety, screen
from ..settings import settings
from .log import log, screenshot

What = str | Path | Target


def target(what: What) -> Target:
    return load(what, settings.images)


def _union(areas: list[Region | None]) -> Region | None:
    """The smallest region holding every area; None (the whole screen) if any of them is the whole screen."""
    if any(area is None for area in areas):
        return None
    left, top = min(a.x for a in areas), min(a.y for a in areas)
    right, bottom = max(a.right for a in areas), max(a.bottom for a in areas)
    return Region(left, top, right - left, bottom - top)


def _look(chosen: list[Target], region: Region | None) -> Match | None:
    """One screen capture covering every target's area, then each target searched in its own part of it."""
    areas = [region if region is not None else one.region for one in chosen]
    pixels, origin = screen.grab(_union(areas))
    if pixels.size == 0:
        return None
    for one, area in zip(chosen, areas, strict=True):
        part, part_origin = pixels, origin
        if area is not None:
            inside = area.intersect(origin)
            if inside is None:
                continue
            x, y = inside.x - origin.x, inside.y - origin.y
            part, part_origin = pixels[y : y + inside.h, x : x + inside.w], inside
        similarity = one.similarity if one.similarity is not None else settings.similarity
        if found := matching.best(one, part, part_origin, similarity):
            return found
    return None


def _usable(whats: tuple[What, ...]) -> list[Target]:
    chosen = []
    for what in whats:
        try:
            chosen.append(target(what))
        except TargetError as error:
            if settings.missing_images != "skip":
                raise
            log(f"skipped: {error}")
    return chosen


def _search(whats: tuple[What, ...], timeout: float, region: Region | None) -> Match | None:
    chosen = _usable(whats)
    if not chosen:
        safety.sleep(timeout)
        return None
    for one in chosen:
        if one._pixels is None:
            raise ValueError(f"{one.label} is a location, there's nothing to look for")
    deadline = time.monotonic() + timeout
    while True:
        safety.check()
        started = time.monotonic()
        if found := _look(chosen, region):
            return found
        if started >= deadline:
            return None
        pause = 1 / settings.scan_rate - (time.monotonic() - started)
        safety.sleep(min(max(pause, 0), max(deadline - time.monotonic(), 0)))


def exists(what: What, timeout: float = 0, region: Region | None = None) -> Match | None:
    """The target if it's on screen, looking for up to `timeout` seconds (0: one look)."""
    found = _search((what,), timeout, region)
    _report("exists", (what,), timeout, found)
    return found


def wait(*whats: What, timeout: float | None = None, region: Region | None = None) -> Match | None:
    """Wait for a target, or the first of several (`match.name` says which). None if time runs out."""
    timeout = settings.timeout if timeout is None else timeout
    found = _search(whats, timeout, region)
    _report("wait", whats, timeout, found)
    return found


def vanish(what: What, timeout: float | None = None, region: Region | None = None) -> bool:
    """True once the target is gone, waiting up to `timeout` seconds."""
    timeout = settings.timeout if timeout is None else timeout
    deadline = time.monotonic() + timeout
    while True:
        if _search((what,), 0, region) is None:
            log(f"vanish {_names((what,))}: gone")
            return True
        if time.monotonic() >= deadline:
            log(f"vanish {_names((what,))}: still there after {timeout}s")
            return False
        safety.sleep(1 / settings.scan_rate)


def find_all(what: What, region: Region | None = None) -> list[Match]:
    """Every place the target is on screen, best first."""
    usable = _usable((what,))
    if not usable or usable[0]._pixels is None:
        return []
    chosen = usable[0]
    pixels, origin = screen.grab(region if region is not None else chosen.region)
    if pixels.size == 0:
        return []
    similarity = chosen.similarity if chosen.similarity is not None else settings.similarity
    return matching.every(chosen, pixels, origin, similarity)


def check(*whats: What) -> list[str]:
    """Names of targets whose image file is missing, e.g. to check every image when a script starts."""
    missing = []
    for what in whats:
        if isinstance(what, Target):
            what = what.image
        if what is not None and find_file(what, settings.images) is None:
            missing.append(str(what))
    return missing


def _names(whats: tuple[What, ...]) -> str:
    return ", ".join(w.label if isinstance(w, Target) else str(w) for w in whats)


def _report(kind: str, whats: tuple[What, ...], timeout: float, found: Match | None) -> None:
    if found is not None:
        log(f"{kind} {_names(whats)}: found {found.name} at {found.x},{found.y} score {found.score:.2f}")
        return
    if timeout > 0:
        log(f"{kind} {_names(whats)}: not found in {timeout}s")
    if settings.screenshot_after and timeout >= settings.screenshot_after:
        screenshot(f"not-found_{_names(whats)}")
