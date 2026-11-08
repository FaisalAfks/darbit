"""Reading text on screen: `d.read`, `d.read_number`, `d.read_time`. Text that can't be read gives None, never an error.

    coins = d.read_number("Shop.Coins")     # a named Region: 4.99M -> 4990000.0
    left = d.read_time(found)               # inside a Match: 02:31 -> 151.0
    name = d.read(d.Region(100, 40, 200, 30))

Each read grabs its area, prepares it (core/reading.py), reads it with the reader settings.reader names
(runtime/readers.py) and is logged and recorded with its confidence, like a search.
"""

import time
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from ..core import geometry
from ..core.reading import Prepare, Reading, characters, parse_number, parse_time, prepare, trim
from ..core.targets import Match, Pattern, Target
from ..errors import TargetError
from ..platform import screen
from ..platform.backend import Reader
from ..settings import settings
from . import find, readers
from .log import log, record

Where = str | Path | Target | Pattern | geometry.Region | Match


@dataclass(frozen=True)
class Spot:
    """Where to read, what it's called in the log, and what its target says about reading it."""

    area: geometry.Region
    label: str
    text: str | None = None
    options: dict | None = None


def spot_of(where: Where) -> Spot | None:
    """Where a read looks: a Region or a Match as they are, a named Region where it is now, a named Image where it's
    found now (None when it isn't on screen)."""
    if isinstance(where, Match):
        return Spot(where.region, where.name or where.target.label, where.target.text, where.target.read)
    if isinstance(where, geometry.Region):
        return Spot(where, f"{where.x},{where.y} {where.w}x{where.h}")
    placed = find.placed_now(where)
    if placed._pixels is not None:
        found = find.exists(where)
        if found is None:
            log(f"read {placed.label}: not on screen")
            return None
        return Spot(found.region, placed.label, placed.text, placed.read)
    if placed.region is None:
        raise TargetError(f"{placed.label} has no region to read in")
    return Spot(placed.region, placed.label, placed.text, placed.read)


def recognise(reader: Reader, pixels: np.ndarray, how: Prepare, allowed: str | None) -> Reading:
    """The text in the pixels: one line (cut to its text) straight to the recogniser, or each line found first.
    A single line that comes back empty or unsure is read again line by line, and the surer of the two kept."""
    pixels = prepare(pixels, how)
    if how.lines:
        return joined(reader.lines(pixels, allowed))
    part = trim(pixels) if how.trim else pixels
    single = reader.line(part, allowed)
    if single.text and single.confidence >= settings.read_confidence:
        return single
    by_lines = joined(reader.lines(pixels, allowed))
    if by_lines.confidence > single.confidence:
        return by_lines
    return single


def joined(found: list[Reading]) -> Reading:
    """Lines read one by one as one text, a line each, with their average confidence."""
    if not found:
        return Reading("", 0.0)
    text = "\n".join(reading.text for reading in found)
    confidence = sum(reading.confidence for reading in found) / len(found)
    return Reading(text, confidence)


def _read(kind: str, where: Where, chars: str | None, usual: str | None) -> str | None:
    spot = spot_of(where)
    if spot is None:
        return None
    reader = readers.current()
    if reader is None:
        return None
    pixels, _ = screen.grab(spot.area)
    if pixels.size == 0:
        log(f"{kind} {spot.label}: nothing on screen there")
        return None
    allowed = characters(chars or spot.text or usual)
    started = time.perf_counter()
    reading = recognise(reader, pixels, readers.prepare_for(spot.options), allowed)
    took = round((time.perf_counter() - started) * 1000, 1)
    counted = bool(reading.text) and reading.confidence >= settings.read_confidence
    text = reading.text if counted else None
    log(
        f"{kind} {spot.label}: {reading.text!r} confidence {reading.confidence:.2f}"
        + ("" if counted else ", too unsure")
    )
    record(
        kind, target=spot.label, text=reading.text, confidence=round(reading.confidence, 3), counted=counted, ms=took
    )
    return text


def read(where: Where, chars: str | None = None) -> str | None:
    """The text in a Region, a Match, a named Region or a named Image (inside where it's found); None if it can't be
    read. `chars` limits it to some characters: "digits", "number", "time" or the characters themselves (default:
    the Region's own `text`, else any)."""
    return _read("read", where, chars, None)


def read_number(where: Where) -> float | None:
    """The number shown there: `1,234`, `4.99M` (4990000.0), `126.62B`, `1.5k`, `12%` (12.0); None if it isn't one."""
    return parse_number(_read("read_number", where, None, "number"))


def read_time(where: Where) -> float | None:
    """The time shown there, in seconds: `02:31` (151.0), `1:02:03`, `2m 30s`, `45s`; None if it isn't one."""
    return parse_time(_read("read_time", where, None, "time"))
