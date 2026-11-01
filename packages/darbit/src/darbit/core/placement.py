"""Placing a target on today's screen: following its window, and resizing it to the current scaling.

A target taken in an app window (its .json has `window` and `origin`) is moved with that window and
scaled by how much wider the window is now, and one with no region of its own is searched only inside the window. A target with only `scale` is resized by the change in
display scaling, its region grown to fit. Anything else, or nothing changed, is used as it is.
See docs/archive/tasks/T22-window-targets.md.
"""

from dataclasses import dataclass, replace

import cv2
import numpy as np

from .geometry import Location, Region
from .targets import Target

SAME = 0.001  # ratios closer to 1 than this are 1


@dataclass(frozen=True)
class Place:
    """The screen today: the app window's content area (None if not known) and the display scaling."""

    window: Region | None = None
    scale: float | None = None


def follows_window(target: Target, place: Place) -> bool:
    """Whether the target was taken in a window that can be found now (not minimised: it has a size)."""
    if target.window is None or target.origin is None or place.window is None:
        return False
    sizes_known = target.window[0] > 0 and target.window[1] > 0
    shown = place.window.w > 0 and place.window.h > 0
    return sizes_known and shown


def ratio(target: Target, place: Place) -> float:
    """How much bigger the target is on screen now than when it was taken.

    The window's width when the target has a window size: that's in real pixels, so it already holds a
    change in scaling. The change in scaling otherwise. Never both.
    """
    if follows_window(target, place):
        return place.window.w / target.window[0]
    if target.scale is not None and place.scale is not None:
        return place.scale / target.scale
    return 1.0


def aspect_changed(target: Target, place: Place) -> bool:
    """Whether the window's shape changed (not just its size) since the target was taken."""
    if not follows_window(target, place):
        return False
    wide_then = target.window[0] / target.window[1]
    wide_now = place.window.w / place.window.h
    return abs(wide_now - wide_then) > 0.02 * wide_then


def placed(target: Target, place: Place, extra: float = 1.0) -> Target:
    """The target as it is on screen now. `extra` multiplies the ratio (for trying nearby sizes).

    The result has no window, origin or scale left, so placing it again changes nothing.
    """
    moves = follows_window(target, place)
    measured = moves or (target.scale is not None and place.scale is not None)
    if not measured:
        extra = 1.0  # nothing to correct: an already placed target, or one with no size saved
    size = ratio(target, place) * extra
    if abs(size - 1) < SAME and not moves:
        return target

    region = target.region
    location = target.location
    if moves:
        if region is not None:
            region = _moved_region(region, target.origin, place.window, size)
        elif target._pixels is not None:
            region = place.window  # taken in the window: it's somewhere in it, so only the window is searched
        if location is not None:
            location = _moved_location(location, target.origin, place.window, size)
    elif region is not None and size > 1:
        region = _grown(region, size)  # where things are is unknown; make room for the bigger image

    pixels = target._pixels
    if pixels is not None and abs(size - 1) >= SAME:
        pixels = resized(pixels, size)
    offset = (target.offset[0] * size, target.offset[1] * size)
    return replace(
        target,
        region=region,
        location=location,
        offset=offset,
        window=None,
        origin=None,
        scale=None,
        _pixels=pixels,
    )


def _moved_region(region: Region, origin: tuple[int, int], window: Region, size: float) -> Region:
    x = window.x + (region.x - origin[0]) * size
    y = window.y + (region.y - origin[1]) * size
    return Region(round(x), round(y), round(region.w * size), round(region.h * size))


def _moved_location(location: Location, origin: tuple[int, int], window: Region, size: float) -> Location:
    x = window.x + (location.x - origin[0]) * size
    y = window.y + (location.y - origin[1]) * size
    return Location(x, y)


def _grown(region: Region, size: float) -> Region:
    """The region made `size` times bigger around its centre."""
    w = round(region.w * size)
    h = round(region.h * size)
    x = region.x - (w - region.w) // 2
    y = region.y - (h - region.h) // 2
    return Region(x, y, w, h)


# resized images by (id of the original, size); the original is kept too, so a reused id is noticed
_resized: dict[tuple[int, float], tuple[np.ndarray, np.ndarray]] = {}


def resized(pixels: np.ndarray, size: float) -> np.ndarray:
    """The image `size` times bigger (or smaller), kept for the next time it's asked for."""
    key = (id(pixels), round(size, 4))
    found = _resized.get(key)
    if found is not None and found[0] is pixels:
        return found[1]
    w = max(1, round(pixels.shape[1] * size))
    h = max(1, round(pixels.shape[0] * size))
    if size < 1:
        smooth = cv2.INTER_AREA  # shrinking: average the pixels
    else:
        smooth = cv2.INTER_LINEAR
    result = cv2.resize(pixels, (w, h), interpolation=smooth)
    if len(_resized) > 512:
        _resized.clear()
    _resized[key] = (pixels, result)
    return result
