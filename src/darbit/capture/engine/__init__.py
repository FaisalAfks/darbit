"""The capture tool's image work, without any UI: what a click selects, and where edges snap.

    prep = prepare(shot)                       # once per freeze
    boxes = candidates(prep, x, y, "region")   # smallest first; click again for the next
    box, guides = snap_box(prep.lines, box, {"right", "bottom"})

See docs/tasks/T08-capture-engine.md.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .select import candidates
from .snap import Lines, lines, snap_box


@dataclass
class Prepared:
    """Everything worked out from one frozen screen, once."""

    shot: np.ndarray
    gray: np.ndarray
    edges: np.ndarray  # Canny, full size
    edges_half: np.ndarray  # Canny at half size, for big rectangles
    lines: Lines


def prepare(shot: np.ndarray) -> Prepared:
    """Work out edges and straight lines for a frozen screen. Budget: 120 ms for 2560x1600."""
    raise NotImplementedError("TODO(T08)")


__all__ = ["Lines", "Prepared", "candidates", "lines", "prepare", "snap_box"]
