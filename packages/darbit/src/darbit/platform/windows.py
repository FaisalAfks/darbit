"""Finding, focusing and closing top-level windows and their apps, through the system's Windows piece.

An app is named by its window title ("Roblox") or by its program file ("chrome.exe", or a full path to it).
"""

from ..core.geometry import Region
from . import backend
from .backend import Window

__all__ = ["Window", "bring_to_front", "close", "in_front", "matching", "region", "windows"]


def windows() -> list[Window]:
    return backend.windows().windows()


def matching(name: str, loose: bool = False) -> list[Window]:
    return backend.windows().matching(name, loose)


def in_front(handle: int) -> bool:
    return backend.windows().in_front(handle)


def bring_to_front(handle: int) -> bool:
    return backend.windows().bring_to_front(handle)


def region(handle: int) -> Region:
    """A window's content area on screen."""
    return backend.windows().region(handle)


def close(name: str, wait: float = 5.0) -> bool:
    return backend.windows().close(name, wait)
