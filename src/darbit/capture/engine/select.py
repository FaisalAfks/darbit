"""Click to select: every sensible box around a point, smallest first. See docs/tasks/T08-capture-engine.md.

Replaces overlay.box_at, which had size caps (20% of the screen, a 900x600 search window, 6% when
growing), so whole menus and windows couldn't be selected.
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Literal

from ...core.geometry import Region

if TYPE_CHECKING:
    from . import Prepared

Kind = Literal["image", "region", "point"]


def candidates(prep: Prepared, x: int, y: int, kind: Kind) -> list[Region]:
    """Boxes around (x, y), smallest first, ending with the whole monitor.

    image:  colour fill, then the areas just outside it (a letter, an icon, a button)
    region: near-rectangular contours on the half-size edge map, from 80x60 up to the monitor
    Near-duplicates (IoU > 0.9) are dropped."""
    raise NotImplementedError("TODO(T08)")
