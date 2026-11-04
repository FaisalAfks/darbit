"""Keeping the bot's window (settings.window) in front. settings.front says when:

- "input" (the default): before every input.
- "always": before every search too.
- "opened": only once, when a window by that name has just appeared (a game reopened behind another window), so
  every other window can be used while the bot runs.

A window that opens behind another one stays there (Windows doesn't let a process in the background take the front),
and a search only sees what's in front."""

from ..platform import windows
from ..settings import settings

_seen: set[int] = set()  # windows already brought forward once, for "opened"


def _bring() -> None:
    """Bring settings.window to the front if it's set, open and behind something."""
    if not settings.window:
        return
    found = windows.matching(settings.window)
    if not found:
        return
    handle = found[0].handle
    if settings.front == "opened":
        if handle in _seen:
            return
        _seen.add(handle)
    if not windows.in_front(handle):
        windows.bring_to_front(handle)


def before_input() -> None:
    if settings.front in ("input", "opened"):
        _bring()


def before_search() -> None:
    if settings.front in ("always", "opened"):
        _bring()
