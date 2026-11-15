"""Opening, closing and switching to apps.

An app is named by its window title ("Game") or by its program ("chrome.exe",
or a full path to it). `App("Game")` keeps the name: `App("Game").window` is its window as a Region.

What `open` opens is logged without the parts that can hold a secret (`shown`): a link stops at its first ?, # or &,
and a path shows only the program's name.
"""

import re
from pathlib import PureWindowsPath

from ..platform import windows
from .log import log
from .region import Region


class App:
    """An app by window title or program, the SikuliX way: `game = App("Game").window`."""

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
    windows.launch(path_or_url)
    log(f"open {shown(path_or_url)}")


_LINK = re.compile(r"^(?P<scheme>[a-zA-Z][a-zA-Z0-9+.-]*)://(?P<rest>.*)$", re.DOTALL)


def shown(path_or_url: str) -> str:
    """What the log and report say was opened. A link keeps its scheme, host and path up to the first ?, # or &
    (a private invite's code or a token sits after them), without a user:password@, and says "…" for what it left
    out. A path shows the program's or file's name only."""
    link = _LINK.match(path_or_url)
    if link is None:
        return PureWindowsPath(path_or_url).name or path_or_url
    rest = link["rest"]
    kept = re.split(r"[?#&]", rest, maxsplit=1)[0]
    host, slash, path = kept.partition("/")
    host = host.rpartition("@")[2]  # never a user:password@
    cut = "…" if len(kept) < len(rest) or "@" in kept.partition("/")[0] else ""
    return f"{link['scheme']}://{host}{slash}{path}{cut}"


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
