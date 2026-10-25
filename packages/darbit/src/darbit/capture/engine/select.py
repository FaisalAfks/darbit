"""Click to select: every sensible box around a point, smallest first. See docs/tasks/T08-capture-engine.md.

    boxes = candidates(prep, x, y, "image")    # every size, smallest first
    at = pick(boxes)                           # a click starts here; clicking again steps to the next

No size caps: the list goes from a letter or an icon up to whole menus, windows and the monitor.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Literal

import cv2
import numpy as np

from ...core.geometry import Region
from .snap import snap_box

if TYPE_CHECKING:
    from . import Prepared

Kind = Literal["image", "region", "point"]

MIN_REGION = (80, 60)  # smallest region candidate, real pixels
MIN_SHAPE = 12  # smallest shape from edges
SQUARENESS = 0.85  # a contour fills at least this much of its bounding box to count as a rectangle
SAME = 0.9  # boxes overlapping more than this (IoU) are the same candidate
FILL_DIFF = 12  # colour difference a fill spreads across
START = (40, 30)  # a click starts on the first box at least this big: a button, not a letter on it


def edges_of(shot: np.ndarray) -> np.ndarray:
    gray = cv2.cvtColor(shot, cv2.COLOR_BGR2GRAY) if shot.ndim == 3 else shot
    return cv2.Canny(gray, 60, 160)


def fill(shot: np.ndarray, x: int, y: int, diff: int = FILL_DIFF) -> Region:
    """The area of similar colour connected to (x, y)."""
    h, w = shot.shape[:2]
    mask = np.zeros((h + 2, w + 2), np.uint8)
    _, _, _, (bx, by, bw, bh) = cv2.floodFill(
        shot, mask, (x, y), 0, (diff,) * 3, (diff,) * 3, 4 | cv2.FLOODFILL_MASK_ONLY | (255 << 8)
    )
    return Region(int(bx), int(by), int(bw), int(bh))


def grow(shot: np.ndarray, inner: Region, x: int, y: int, limit: float = 1.0) -> Region | None:
    """The biggest area of one colour just outside `inner` that contains it, up to `limit` of the screen."""
    h, w = shot.shape[:2]
    best = None
    for px, py in ((inner.x - 3, y), (inner.right + 2, y), (x, inner.y - 3), (x, inner.bottom + 2)):
        if not (0 <= px < w and 0 <= py < h):
            continue
        around = fill(shot, px, py)
        inside = (
            around.x <= inner.x
            and around.y <= inner.y
            and around.right >= inner.right
            and around.bottom >= inner.bottom
        )
        bigger = around.w * around.h > inner.w * inner.h
        small_enough = around.w * around.h <= limit * w * h
        if inside and bigger and small_enough and (best is None or around.w * around.h > best.w * best.h):
            best = around
    return best


def shape_at(shot: np.ndarray, x: int, y: int, around: tuple[int, int] = (900, 600)) -> Region | None:
    """The smallest closed shape around (x, y), from the edges near it."""
    h, w = shot.shape[:2]
    left, top = max(0, x - around[0] // 2), max(0, y - around[1] // 2)
    right, bottom = min(w, left + around[0]), min(h, top + around[1])
    edges = cv2.dilate(edges_of(shot[top:bottom, left:right]), np.ones((3, 3), np.uint8))
    contours, _ = cv2.findContours(edges, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
    px, py = x - left, y - top
    best = None
    limit = 0.7 * (right - left) * (bottom - top)
    for contour in contours:
        bx, by, bw, bh = cv2.boundingRect(contour)
        if bw < MIN_SHAPE or bh < MIN_SHAPE or bw * bh > limit:
            continue
        if bx <= px < bx + bw and by <= py < by + bh and (best is None or bw * bh < best[2] * best[3]):
            best = (bx, by, bw, bh)
    if best is None:
        return None
    bx, by, bw, bh = best
    return Region(left + bx, top + by, bw, bh)


def rectangles(edges_half: np.ndarray, x: int, y: int, minimum: tuple[int, int] = MIN_REGION) -> list[Region]:
    """Near-rectangular outlines around (x, y) anywhere on the screen, from the half-size edge map:
    panels, windows, lists. In full-size pixels."""
    edges = cv2.dilate(edges_half, np.ones((3, 3), np.uint8))
    contours, _ = cv2.findContours(edges, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
    hx, hy = x // 2, y // 2
    found = []
    for contour in contours:
        bx, by, bw, bh = cv2.boundingRect(contour)
        if bw * 2 < minimum[0] or bh * 2 < minimum[1] or not (bx <= hx < bx + bw and by <= hy < by + bh):
            continue
        square = cv2.contourArea(contour) >= SQUARENESS * bw * bh
        corners = len(cv2.approxPolyDP(contour, 0.02 * cv2.arcLength(contour, True), True)) == 4
        if square or corners:
            found.append(Region(bx * 2, by * 2, bw * 2, bh * 2))
    return found


def _iou(a: Region, b: Region) -> float:
    both = a.intersect(b)
    if both is None:
        return 0.0
    shared = both.w * both.h
    return shared / (a.w * a.h + b.w * b.h - shared)


def _distinct(boxes: list[Region]) -> list[Region]:
    """Near-duplicates dropped, keeping the first one given (callers list exact boxes first), smallest first."""
    kept: list[Region] = []
    for box in boxes:
        if box.w >= 3 and box.h >= 3 and all(_iou(box, k) <= SAME for k in kept):
            kept.append(box)
    return sorted(kept, key=lambda b: b.w * b.h)


def candidates(prep: Prepared, x: int, y: int, kind: Kind) -> list[Region]:
    """Boxes around (x, y), smallest first, ending with the whole screen.

    image:  the colour fill (a button's background gives the button), the areas just outside it, the rectangles
            a region would get, and the smallest shape traced from edges
    region: rectangles from the half-size edge map, from 80x60 up to the screen
    Near-duplicates (IoU > 0.9) are dropped."""
    shot = prep.shot
    h, w = shot.shape[:2]
    x, y = min(max(0, x), w - 1), min(max(0, y), h - 1)
    everywhere = {"left", "top", "right", "bottom"}
    # half-size outlines are a pixel or two off: put them on the real borders
    outlines = [snap_box(prep.lines, r, everywhere, reach=3)[0] for r in rectangles(prep.edges_half, x, y)]
    boxes: list[Region] = list(outlines)  # first: on a tie, the box with its border wins
    if kind == "image":
        first = fill(shot, x, y)
        if first.w * first.h <= 0.2 * w * h:  # a huge fill is the background around an icon, not a thing
            boxes.append(first)
            step = first
            for _ in range(6):
                if (step := grow(shot, step, x, y)) is None:
                    break
                boxes.append(step)
    if kind == "image" and (shape := shape_at(shot, x, y)) is not None:
        boxes.append(shape)  # traced from edge pixels: last, so exact boxes win over it
    screen = Region(0, 0, w, h)
    return [b for b in _distinct(boxes) if _iou(b, screen) <= SAME] + [screen]


def pick(boxes: list[Region], start: tuple[int, int] = START) -> int:
    """Which candidate a click selects first: the smallest at least `start` big, a button rather than a letter
    on it. A small first box is kept when the next is barely bigger (its own outline), so thin things like a
    scrollbar handle are selected too. Smaller ones stay in the list for "smaller"."""
    if len(boxes) > 1 and boxes[1].w * boxes[1].h < 4 * boxes[0].w * boxes[0].h:
        return 0
    return next((i for i, b in enumerate(boxes) if b.w >= start[0] and b.h >= start[1]), 0)
