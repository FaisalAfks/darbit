"""Screen captures in real pixels, through the system's Screen piece (platform/backend.py)."""

import numpy as np

from ..core.geometry import Region
from . import backend


def enable_dpi_awareness() -> None:
    """Work in real pixels on scaled displays (150% etc.). Must run before any capture, window or input call."""
    try:
        backend.screen().enable_dpi_awareness()
    except backend.NotSupported:
        pass


def desktop() -> Region:
    """Every monitor together."""
    return backend.screen().desktop()


def monitors() -> list[Region]:
    return backend.screen().monitors()


def grab(region: Region | None = None) -> tuple[np.ndarray, Region]:
    """Capture a region (the whole desktop for None) as BGR pixels, clipped to the screen. Returns the pixels and
    the region actually captured."""
    return backend.screen().grab(region)


def scale_at(x: int, y: int) -> float:
    """The display scaling at a point, e.g. 1.5 for 150%."""
    return backend.screen().scale_at(x, y)
