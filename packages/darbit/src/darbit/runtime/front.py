"""Keeping the bot's window (settings.window) in front: before input, and with settings.front = "always" before
searches too. A window that just opened behind another one stays there (Windows doesn't let a process in the
background take the front), and a search only sees what's in front."""

from ..platform import windows
from ..settings import settings


def _bring() -> None:
    """Bring settings.window to the front if it's set, open and behind something."""
    if not settings.window:
        return
    found = windows.matching(settings.window)
    if found and not windows.in_front(found[0].handle):
        windows.bring_to_front(found[0].handle)


def before_input() -> None:
    _bring()


def before_search() -> None:
    if settings.front == "always":
        _bring()
