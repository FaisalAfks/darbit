"""Finding, focusing, opening and closing apps and their windows, through the system's Windows piece.

An app is named by its window title ("Game") or by its program file ("chrome.exe", or a full path to it).
"""

from ..core.geometry import Region
from . import backend, real
from .backend import Window

__all__ = [
    "Window",
    "bring_to_front",
    "close",
    "in_front",
    "keep_out_of_captures",
    "launch",
    "matching",
    "region",
    "windows",
]


def windows() -> list[Window]:
    return backend.windows().windows()


def matching(name: str, loose: bool = False) -> list[Window]:
    return backend.windows().matching(name, loose)


def in_front(handle: int) -> bool:
    return backend.windows().in_front(handle)


def bring_to_front(handle: int) -> bool:
    real.refuse("windows.bring_to_front")
    return backend.windows().bring_to_front(handle)


def region(handle: int) -> Region:
    """A window's content area on screen."""
    return backend.windows().region(handle)


def close(name: str, wait: float = 5.0) -> bool:
    real.refuse("windows.close")
    return backend.windows().close(name, wait)


def launch(path_or_url: str) -> None:
    """Open a program, file or link the way double-clicking it would."""
    real.refuse("windows.launch")
    backend.windows().launch(path_or_url)


def keep_out_of_captures(handle: int) -> bool:
    """Leave one of darbit's own windows out of every screen capture, darbit's included: an overlay drawn over the
    game mustn't cover what a bot looks for. False where the system can't."""
    return backend.windows().keep_out_of_captures(handle)
