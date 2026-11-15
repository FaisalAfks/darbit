"""Results worked out from files, kept until those files change.

The Studio asks for the Overview every couple of seconds while a bot runs. Some of its parts look at every file in a
folder (the newest screenshot, which of the setup guide's pictures are taken), and those folders rarely change. A
FileCache keeps such a result with a stamp of the files and folders it came from (their modified time and size) and
works it out again only when the stamp changes, or after MAX_AGE seconds in case a change didn't touch the stamp."""

import time
from collections.abc import Callable, Iterable
from pathlib import Path
from typing import TypeVar

MAX_AGE = 60  # seconds a kept result is used at most, even when its files look unchanged

Value = TypeVar("Value")


def stamp(paths: Iterable[Path]) -> tuple:
    """Each path's modified time and size, None for one that's missing. A folder's changes when a file in it is
    added, removed or renamed."""
    found: list = []
    for path in paths:
        try:
            info = path.stat()
            found.append((info.st_mtime_ns, info.st_size))
        except OSError:
            found.append(None)
    return tuple(found)


class FileCache:
    """Results by key, each kept with the stamp of the paths it was worked out from."""

    def __init__(self) -> None:
        self._kept: dict[object, tuple[tuple, float, object]] = {}

    def get(self, key: object, paths: Iterable[Path], work: Callable[[], Value]) -> Value:
        """The kept result for `key` while `paths` are unchanged and it's younger than MAX_AGE, else `work()`."""
        mark = stamp(paths)
        now = time.monotonic()
        kept = self._kept.get(key)
        if kept is not None and kept[0] == mark and now - kept[1] < MAX_AGE:
            return kept[2]
        value = work()
        self._kept[key] = (mark, now, value)
        return value

    def clear(self) -> None:
        self._kept.clear()
