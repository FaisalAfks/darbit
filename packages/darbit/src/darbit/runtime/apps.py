"""Opening, closing and switching to apps.

An app is named by its window title ("Roblox") or by its program ("chrome.exe",
or a full path to it).
"""

import os

from ..core.geometry import Region
from ..platform import windows
from .log import log


def open(path_or_url: str) -> None:
    """Open a program, file or link the way double-clicking it would."""
    os.startfile(path_or_url)
    log(f"open {path_or_url}")


def close(app: str) -> bool:
    """Close an app's windows. True if it had any."""
    closed = windows.close(app)
    log(f"close {app}: {'closed' if closed else 'not running'}")
    return closed


def running(app: str) -> bool:
    """Whether the app has a window open."""
    return bool(windows.matching(app))


def focus(app: str) -> bool:
    """Bring the app's window to the front. A title may be part of the window's title here."""
    found = windows.matching(app, loose=True)
    if not found:
        return False
    return windows.bring_to_front(found[0].handle)


def window(app: str) -> Region | None:
    """The app's window area on screen, or None if it isn't open."""
    found = windows.matching(app, loose=True)
    return windows.region(found[0].handle) if found else None
