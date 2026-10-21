"""Snapping: box edges pulled onto straight lines nearby. See docs/tasks/T08-capture-engine.md.

A line is a straight run of boundaries between two pixels where the brightness jumps, so a
line's position is exact: a vertical line at x=300 is between pixels 299 and 300. A drawn
border has two of them, its outer and its inner side.

Only the edges being moved snap, and only to a line that runs along most of that side, so a
texture or a letter doesn't pull a box. The overlay gets `lines()` once per freeze and snaps in
the window (ui/src/apps/capture/snap.ts) with the same rules; both pass
tests/data/capture/snap_cases.json.
"""
from __future__ import annotations

from typing import Literal, TypedDict

import numpy as np

from ...core.geometry import Region

Edge = Literal["left", "top", "right", "bottom"]
Guide = tuple[int, int, int, int]  # x0, y0, x1, y1

STEP = 24  # brightness jump (0-255) that makes a boundary
OVERLAP = 0.3  # a line must run along at least this share of the side it snaps
BAND = 8  # lines this close together are the two sides of one border


class Lines(TypedDict):
    h: list[tuple[int, int, int]]  # y, x0, x1: between rows y-1 and y, from x0 to x1 (exclusive)
    v: list[tuple[int, int, int]]  # x, y0, y1: between columns x-1 and x, from y0 to y1 (exclusive)


def _runs(mask: np.ndarray, length: int) -> list[tuple[int, int, int]]:
    """Runs of set cells along each row: (row, start, end), at least `length` long."""
    padded = np.zeros((mask.shape[0], mask.shape[1] + 2), np.int8)
    padded[:, 1:-1] = mask
    change = np.diff(padded, axis=1)
    rows, starts = np.nonzero(change == 1)
    _, ends = np.nonzero(change == -1)  # same order as starts: row by row, left to right
    keep = ends - starts >= length
    return list(zip(rows[keep].tolist(), starts[keep].tolist(), ends[keep].tolist(), strict=True))


def lines(gray: np.ndarray, length: int = 16, most: int = 4000, step: int = STEP) -> Lines:
    """Straight horizontal and vertical boundaries at least `length` px long, the longest `most`."""
    g = gray.astype(np.int16)
    across = np.abs(np.diff(g, axis=1)) >= step  # (h, w-1): between column x and x+1
    down = np.abs(np.diff(g, axis=0)) >= step  # (h-1, w): between row y and y+1
    v = [(x + 1, y0, y1) for x, y0, y1 in _runs(np.ascontiguousarray(across.T), length)]
    h = [(y + 1, x0, x1) for y, x0, x1 in _runs(down, length)]
    h.sort(key=lambda r: r[1] - r[2])
    v.sort(key=lambda r: r[1] - r[2])
    return {"h": h[:most], "v": v[:most]}


def _overlap(a0: int, a1: int, b0: int, b1: int) -> int:
    return max(0, min(a1, b1) - max(a0, b0))


def _nearest(segments: list[tuple[int, int, int]], at: int, span: tuple[int, int], reach: int,
             side: int) -> tuple[int, int, int] | None:
    """The line nearest to `at` (within reach) that runs along at least OVERLAP of `span`; longer wins ties.
    Lines on `side` of it (-1 lower, +1 higher) within BAND are the same border, so the walk goes to the
    last of them: the border's outer side when snapping outward, its inner side when inward."""
    need = OVERLAP * (span[1] - span[0])
    usable = [s for s in segments if _overlap(s[1], s[2], *span) >= need]
    near = [s for s in usable if abs(s[0] - at) <= reach]
    if not near:
        return None
    best = min(near, key=lambda s: (abs(s[0] - at), s[1] - s[2]))
    while beyond := [s for s in usable if 0 < (s[0] - best[0]) * side <= BAND]:
        best = min(beyond, key=lambda s: abs(s[0] - best[0]))
    return best


def snap_box(found: Lines, box: Region, moving: set[Edge] | frozenset[Edge], reach: int = 6,
             border: Literal["include", "exclude"] = "include") -> tuple[Region, list[Guide]]:
    """Move only the `moving` edges, each onto the nearest line within `reach` that runs along at least 30% of
    that side. With border="include" a border is kept in the box (edges go to its outer side), with "exclude"
    left out (its inner side). Returns the box and the lines it snapped to, for drawing."""
    left, top, right, bottom = box.x, box.y, box.right, box.bottom
    out = 1 if border == "include" else -1  # walk across a border outward from the box, or inward
    guides: list[Guide] = []
    if "left" in moving and (s := _nearest(found["v"], left, (top, bottom), reach, -out)):
        left = s[0]
        guides.append((s[0], s[1], s[0], s[2]))
    if "right" in moving and (s := _nearest(found["v"], right, (top, bottom), reach, out)):
        right = s[0]
        guides.append((s[0], s[1], s[0], s[2]))
    if "top" in moving and (s := _nearest(found["h"], top, (left, right), reach, -out)):
        top = s[0]
        guides.append((s[1], s[0], s[2], s[0]))
    if "bottom" in moving and (s := _nearest(found["h"], bottom, (left, right), reach, out)):
        bottom = s[0]
        guides.append((s[1], s[0], s[2], s[0]))
    if right - left < 1 or bottom - top < 1:
        return box, []
    return Region(left, top, right - left, bottom - top), guides
