"""The capture tool's image work, without any UI: what a click selects, and where edges snap.

    prep = prepare(shot)                       # once per freeze
    boxes = candidates(prep, x, y, "region")   # smallest first
    box = boxes[pick(boxes)]                   # where a click starts; click again for the next
    box, guides = snap_box(prep.lines, box, {"right", "bottom"})

See docs/archive/tasks/T08-capture-engine.md.
"""

from dataclasses import dataclass

import cv2
import numpy as np

from .select import candidates, edges_of, pick
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
    """Work out edges and straight lines for a frozen screen."""
    gray = cv2.cvtColor(shot, cv2.COLOR_BGR2GRAY)
    half = cv2.resize(gray, (gray.shape[1] // 2, gray.shape[0] // 2), interpolation=cv2.INTER_AREA)
    return Prepared(shot, gray, edges_of(gray), edges_of(half), lines(gray))


__all__ = ["Lines", "Prepared", "candidates", "lines", "pick", "prepare", "snap_box"]
