"""Highlight: show where targets are found, with their scores, like SikuliX's highlight() for many at once.

    d.highlight("Gui.Play", "Gui.Bag")          # boxes and scores over the screen for 3 seconds

Without the `app` extra it only logs the scores. Never raises. See docs/tasks/T11-highlight.md.
"""
from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass

from ..core.geometry import Region
from ..core.targets import Match
from .find import What


@dataclass(frozen=True)
class Hit:
    name: str
    match: Match | None  # None: not seen
    elsewhere: float  # the best score outside its own spot (risky when high)
    verdict: str  # "ok", "risky", "missing"


def scan(*targets: What, region: Region | None = None) -> Iterator[Hit]:
    """One screen grab; each target searched in its own region (half size first without one); hits as they
    come, from a thread pool."""
    raise NotImplementedError("TODO(T11)")


def highlight(*targets: What, seconds: float = 3, region: Region | None = None) -> list[Match]:
    """Show the targets found on screen with their scores for `seconds`. Returns what was found."""
    raise NotImplementedError("TODO(T11)")
