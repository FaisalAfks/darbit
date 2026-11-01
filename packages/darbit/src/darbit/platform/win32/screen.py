"""Screen captures in real pixels."""

import ctypes
import threading
from ctypes import wintypes

import mss
import numpy as np

from ...core.geometry import Region

_MSS = getattr(mss, "MSS", None) or mss.mss
_local = threading.local()


def enable_dpi_awareness() -> None:
    """Work in real pixels on scaled displays (150% etc.). Must run before any capture, window or input call."""
    try:
        if not ctypes.windll.user32.SetProcessDpiAwarenessContext(ctypes.c_void_p(-4)):
            ctypes.windll.shcore.SetProcessDpiAwareness(2)
    except (AttributeError, OSError):
        pass


def _sct():
    # mss handles aren't thread-safe, so each thread gets its own
    if not hasattr(_local, "sct"):
        _local.sct = _MSS()
    return _local.sct


def desktop() -> Region:
    """Every monitor together."""
    m = _sct().monitors[0]
    return Region(m["left"], m["top"], m["width"], m["height"])


def monitors() -> list[Region]:
    return [Region(m["left"], m["top"], m["width"], m["height"]) for m in _sct().monitors[1:]]


def grab(region: Region | None = None) -> tuple[np.ndarray, Region]:
    """Capture a region (the whole desktop for None) as BGR pixels, clipped to the screen. Returns the pixels and the region actually captured."""
    whole = desktop()
    region = whole if region is None else region.intersect(whole)
    if region is None:
        return np.zeros((0, 0, 3), np.uint8), Region(0, 0, 0, 0)
    shot = _sct().grab({"left": region.x, "top": region.y, "width": region.w, "height": region.h})
    return np.ascontiguousarray(np.asarray(shot)[:, :, :3]), region


MONITOR_DEFAULTTONEAREST = 2
MDT_EFFECTIVE_DPI = 0


def scale_at(x: int, y: int) -> float:
    """Windows' display scaling at a point, e.g. 1.5 for 150%."""
    user32 = ctypes.windll.user32
    user32.MonitorFromPoint.argtypes = [wintypes.POINT, wintypes.DWORD]
    user32.MonitorFromPoint.restype = wintypes.HMONITOR
    monitor = user32.MonitorFromPoint(wintypes.POINT(x, y), MONITOR_DEFAULTTONEAREST)
    dpi_x, dpi_y = ctypes.c_uint(), ctypes.c_uint()
    try:
        failed = ctypes.windll.shcore.GetDpiForMonitor(
            monitor, MDT_EFFECTIVE_DPI, ctypes.byref(dpi_x), ctypes.byref(dpi_y)
        )
    except OSError:  # no shcore.dll: Windows older than 8.1
        return 1.0
    if failed or not dpi_x.value:
        return 1.0
    return dpi_x.value / 96
