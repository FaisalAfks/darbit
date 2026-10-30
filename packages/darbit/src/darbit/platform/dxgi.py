"""Screen capture with DXGI Desktop Duplication: faster than mss, and free when nothing changed.

screen.grab() picks it with settings.capture = "auto" and falls back to mss on any error.
See docs/archive/tasks/T21-fast-capture.md.
"""

import numpy as np

from ..core.geometry import Region


class Duplication:
    """One monitor's duplication, kept open between grabs."""

    def __init__(self, monitor: int = 0) -> None:
        raise NotImplementedError("TODO(T21)")

    def grab(self, region: Region | None = None) -> tuple[np.ndarray, Region]:
        """BGR pixels of the region; the last frame again when the screen hasn't changed."""
        raise NotImplementedError("TODO(T21)")
