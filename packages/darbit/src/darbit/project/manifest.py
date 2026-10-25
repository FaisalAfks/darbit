"""darbit.toml: a bot's name, version, entry, game window, accent, and its darbit settings.
See docs/tasks/T17-projects.md."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class Project:
    folder: Path
    name: str
    version: str = "0.0.0"
    darbit: str = ""  # the darbit versions it needs, e.g. ">=0.5,<0.6"
    entry: str = "bot.py"
    window: str | None = None
    accent: str | None = None
    settings: dict = field(default_factory=dict)  # layer 2 of darbit's settings
    images: list[str] = field(default_factory=lambda: ["images"])
    keys: dict = field(default_factory=dict)  # keymap overrides


def find(start: Path) -> Path | None:
    """The nearest folder with a darbit.toml, from `start` upward."""
    raise NotImplementedError("TODO(T17)")


def load(folder: Path) -> Project:
    raise NotImplementedError("TODO(T17)")
