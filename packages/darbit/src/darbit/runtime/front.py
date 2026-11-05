"""Keeping the bot's window (settings.window) in front before input. A window that opens behind another one stays
there (Windows doesn't let a process in the background take the front)."""

from ..platform import windows
from ..settings import settings


def before_input() -> None:
    """Bring settings.window to the front if it's set, open and behind something."""
    if not settings.window:
        return
    found = windows.matching(settings.window)
    if found and not windows.in_front(found[0].handle):
        windows.bring_to_front(found[0].handle)
