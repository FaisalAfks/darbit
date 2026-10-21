"""Opening the capture tool from a bot. See docs/tasks/T12-setup-guide.md.

    d.capture("Event.Banner", say="Box this week's event banner")   # blocks until saved or cancelled
    d.guide("guide.toml")                                          # first-run setup

Both need the `ui` extra; without it they log what's missing and return None.
"""
from __future__ import annotations

from pathlib import Path
from typing import Literal

from ..core.geometry import Region
from ..core.targets import Target


def capture(name: str, kind: Literal["image", "region", "location"] = "image", say: str | None = None,
            region: Region | str | None = None) -> Target | None:
    """Freeze the screen for one target, with the bot's own text. Returns the saved target, or None."""
    raise NotImplementedError("TODO(T12)")


def guide(path: str | Path = "guide.toml", say: str | None = None, only: list[str] | None = None) -> bool:
    """Show the setup guide card until the user presses Done. True when everything is captured."""
    raise NotImplementedError("TODO(T12)")
