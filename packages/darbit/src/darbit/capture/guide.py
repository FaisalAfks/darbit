"""Setup guides: an ordered walk-through of what to capture for a bot. See docs/tasks/T12-setup-guide.md.

guide = load(Path("guide.toml"))
progress(guide, Path("images"))      # what's done, what's next
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

ItemKind = Literal["image", "images", "region", "location"]


@dataclass
class Item:
    kind: ItemKind
    names: list[str]  # one name, or many for `images`
    say: str = ""
    within: str | None = None  # `in`: a region target's name
    point: str | tuple[int, int] | None = None  # "center" or an offset
    order: Literal["any", "list"] = "any"


@dataclass
class Screen:
    name: str
    say: str = ""
    example: str | None = None  # a picture of the screen
    take: list[Item] = field(default_factory=list)


@dataclass
class Guide:
    title: str
    say: str = ""
    screens: list[Screen] = field(default_factory=list)


@dataclass
class Progress:
    done: int
    total: int
    current: tuple[Screen, Item, str] | None  # the next thing to take: its screen, item and name


def load(path: Path) -> Guide:
    """Read and check a guide.toml. Errors name the screen and item."""
    raise NotImplementedError("TODO(T12)")


def progress(guide: Guide, images: Path) -> Progress:
    """Done = the target's files exist. Items with order = "list" are taken strictly in order."""
    raise NotImplementedError("TODO(T12)")


def convert_list(path: Path) -> Guide:
    """An old capture list (capture.txt) as a guide: [headers] become screens, # comments become `say`."""
    raise NotImplementedError("TODO(T12)")
