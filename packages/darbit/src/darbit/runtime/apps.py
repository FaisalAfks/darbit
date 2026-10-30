"""Opening, closing and switching to apps.

An app is named by its window title ("Roblox") or by its program ("chrome.exe",
or a full path to it). `App("Roblox")` keeps the name: `App("Roblox").window` is its window as a Region.
"""

import os

from ..platform import windows
from .log import log
from .region import Region


class App:
    """An app by window title or program, the SikuliX way: `game = App("Roblox").window`."""

    def __init__(self, name: str) -> None:
        self.name = name

    @property
    def window(self) -> Region | None:
        """Its window area on screen, to search and click inside; None if it isn't open."""
        return window(self.name)

    @property
    def running(self) -> bool:
        return running(self.name)

    def focus(self) -> bool:
        return focus(self.name)

    def close(self) -> bool:
        return close(self.name)

    def open(self) -> None:
        """Start it: the name is a program, file or link here."""
        open(self.name)


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
    if not found:
        return None
    return Region.of(windows.region(found[0].handle))
