"""Snapping: box edges pulled onto straight lines nearby. See docs/tasks/T08-capture-engine.md.

The overlay gets `lines()` once per freeze and snaps in the window (ui/src/apps/capture/snap.ts),
with the same rules as snap_box here; both pass tests/data/capture/snap_cases.json.
"""
from __future__ import annotations

from typing import Literal, TypedDict

import numpy as np

from ...core.geometry import Region

Edge = Literal["left", "top", "right", "bottom"]


class Lines(TypedDict):
    h: list[tuple[int, int, int]]  # y, x0, x1
    v: list[tuple[int, int, int]]  # x, y0, y1


def lines(edges: np.ndarray, length: int = 16, most: int = 4000) -> Lines:
    """Straight horizontal and vertical segments at least `length` px long, strongest `most`."""
    raise NotImplementedError("TODO(T08): open Canny with 1xL and Lx1 kernels, then run lengths")


def snap_box(found: Lines, box: Region, moving: set[Edge], reach: int = 6,
             border: Literal["include", "exclude"] = "include") -> tuple[Region, list[tuple[int, int, int, int]]]:
    """Move only the `moving` edges, each onto the nearest line within `reach` that overlaps that side by at
    least 30% of its length. Returns the box and the guide lines it snapped to (x0, y0, x1, y1)."""
    raise NotImplementedError("TODO(T08)")
