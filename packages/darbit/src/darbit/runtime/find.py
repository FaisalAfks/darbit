"""Looking for targets on screen. Not finding something returns None or False, never an error.

Every search loads its targets, places them on today's screen (core/placement.py: following their
window, resized to the scaling), then looks. A placed target that isn't found is tried once at nearby
sizes, and a size that works is kept for that target.
"""

import threading
import time
from pathlib import Path

from ..core.geometry import Region
from ..core.placement import SAME, Place, aspect_changed, placed, ratio
from ..core.targets import Match, Target, find_file, load
from ..errors import TargetError
from ..platform import safety, screen, windows
from ..settings import settings
from . import matchers
from .log import log, record, screenshot

What = str | Path | Target


NEARBY = (0.95, 1.05, 0.9, 1.1)  # sizes tried when a resized target isn't found
NEARBY_EVERY = 60  # seconds between such tries for one target, until a size works

_adjust: dict[str, float] = {}  # a nearby size that worked, per target
_tried: dict[str, float] = {}  # when each target was last tried at nearby sizes
_warned: set[str] = set()  # targets already warned about a window of another shape


def target(what: What) -> Target:
    """A target loaded from its files, as it was taken (not placed on today's screen)."""
    return load(what, settings.images)


def where_now(targets: list[Target]) -> Place:
    """Where the app window is and the display scaling, looked up only when a target needs them."""
    needs_window = False
    needs_scale = False
    for one in targets:
        if one.window is not None and one.origin is not None:
            needs_window = True
        if one.scale is not None:
            needs_scale = True
    window = None
    if needs_window and settings.window:
        found = windows.matching(settings.window, loose=True)
        if found:
            window = windows.region(found[0].handle)
            if window.w <= 0 or window.h <= 0:
                window = None  # minimised: targets stay as they were taken
    scale = None
    if needs_scale:
        spot = window
        for one in targets:
            if spot is None and one.region is not None:
                spot = one.region
        if spot is not None:
            middle = spot.center
            scale = screen.scale_at(round(middle.x), round(middle.y))
        else:
            scale = screen.scale_at(0, 0)  # the main screen
    return Place(window, scale)


def place(one: Target, now: Place) -> Target:
    """A loaded target placed on today's screen, with the nearby size that worked for it, if any."""
    if aspect_changed(one, now) and one.label not in _warned:
        _warned.add(one.label)
        log(f"{one.label}: the window's shape changed since it was taken; it may need taking again")
    return placed(one, now, _adjust.get(one.label, 1.0))


def _union(areas: list[Region | None]) -> Region | None:
    """The smallest region holding every area; None (the whole screen) if any of them is the whole screen."""
    if any(area is None for area in areas):
        return None
    left, top = min(a.x for a in areas), min(a.y for a in areas)
    right, bottom = max(a.right for a in areas), max(a.bottom for a in areas)
    return Region(left, top, right - left, bottom - top)


def _look(chosen: list[Target], region: Region | None) -> tuple[Match | None, Match | None]:
    """One screen capture covering every target's area, then each target searched in its own part of it.
    Returns what was found, and the closest spot even when nothing scored high enough."""
    areas = [region if region is not None else one.region for one in chosen]
    pixels, origin = screen.grab(_union(areas))
    closest: Match | None = None
    if pixels.size == 0:
        return None, None
    for one, area in zip(chosen, areas, strict=True):
        part, part_origin = pixels, origin
        if area is not None:
            inside = area.intersect(origin)
            if inside is None:
                continue
            x, y = inside.x - origin.x, inside.y - origin.y
            part, part_origin = pixels[y : y + inside.h, x : x + inside.w], inside
        similarity = one.similarity if one.similarity is not None else settings.similarity
        best = matchers.current().closest(one, part, part_origin, similarity, matchers.options_for(one))
        if best is not None and best.score >= similarity:
            return best, best
        if best is not None and (closest is None or best.score > closest.score):
            closest = best
    return None, closest


def _usable(whats: tuple[What, ...]) -> list[Target]:
    """The targets loaded and placed on today's screen."""
    loaded = _loaded(whats)
    now = where_now(loaded)
    chosen = []
    for one in loaded:
        chosen.append(place(one, now))
    return chosen


def _loaded(whats: tuple[What, ...]) -> list[Target]:
    chosen = []
    for what in whats:
        try:
            chosen.append(target(what))
        except TargetError as error:
            if settings.missing_images != "skip":
                raise
            log(f"skipped: {error}")
    return chosen


_closest = threading.local()  # the closest spot of the last search that found nothing, for the report


def _search(whats: tuple[What, ...], timeout: float, region: Region | None) -> Match | None:
    _closest.match = None
    loaded = _loaded(whats)
    if not loaded:
        safety.sleep(timeout)
        return None
    now = where_now(loaded)
    chosen = []
    for one in loaded:
        chosen.append(place(one, now))
    for one in chosen:
        if one._pixels is None:
            raise ValueError(f"{one.label} is a location, there's nothing to look for")
    deadline = time.monotonic() + timeout
    while True:
        safety.check()
        started = time.monotonic()
        found, closest = _look(chosen, region)
        if found is not None:
            return found
        if closest is not None and (_closest.match is None or closest.score > _closest.match.score):
            _closest.match = closest
        if started >= deadline:
            return _nearby_sizes(loaded, now, region)
        pause = 1 / settings.scan_rate - (time.monotonic() - started)
        safety.sleep(min(max(pause, 0), max(deadline - time.monotonic(), 0)))


def _nearby_sizes(loaded: list[Target], now: Place, region: Region | None) -> Match | None:
    """One look at nearby sizes for resized targets not tried in the last minute; a size that works is kept.

    A target that simply isn't on screen yet is tried again a minute later, not on every look.
    """
    resized = []
    clock = time.monotonic()
    for one in loaded:
        if one._pixels is None or one.label in _adjust:
            continue
        if abs(ratio(one, now) - 1) < SAME:
            continue
        last = _tried.get(one.label)
        if last is not None and clock - last < NEARBY_EVERY:
            continue
        _tried[one.label] = clock
        resized.append(one)
    if not resized:
        return None
    for extra in NEARBY:
        tries = []
        for one in resized:
            tries.append(placed(one, now, extra))
        found, _ = _look(tries, region)
        if found is not None:
            _adjust[found.target.label] = extra
            log(f"{found.target.label}: found at {extra:.0%} of its expected size; keeping that size")
            return found
    return None


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
    return matchers.current().every(chosen, pixels, origin, similarity, 100, matchers.options_for(chosen))


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
    names = _names(whats)
    if found is not None:
        log(f"{kind} {names}: found {found.name} at {found.x},{found.y} score {found.score:.2f}")
        record(
            kind, targets=names, timeout=timeout, found=found.name, score=round(found.score, 3), at=[found.x, found.y]
        )
        return
    closest = getattr(_closest, "match", None)
    near = f", closest {closest.name} {closest.score:.2f} at {closest.x},{closest.y}" if closest else ""
    if timeout > 0:
        log(f"{kind} {names}: not found in {timeout}s{near}")
    shot = None
    if settings.screenshot_after and timeout >= settings.screenshot_after:
        shot = screenshot(f"not-found_{names}")
    record(
        kind,
        targets=names,
        timeout=timeout,
        found=None,
        closest=round(closest.score, 3) if closest else None,
        closest_name=closest.name if closest else None,
        at=[closest.x, closest.y] if closest else None,
        screenshot=shot,
    )
