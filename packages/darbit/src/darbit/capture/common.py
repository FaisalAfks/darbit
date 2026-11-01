"""What capturing shares: the items to take, a capture's result, and capture lists on disk."""

from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

from ..core import matching
from ..core.geometry import Location, Region

KINDS = ("image", "location", "region")


@dataclass(frozen=True)
class Item:
    """One thing to capture: kind is "image", "location" or "region"."""

    name: str
    kind: str = "image"
    note: str = field(default="", compare=False)  # what it is, shown while capturing
    screen: str = field(default="", compare=False)  # the screen it's on, from a [Screen] line in the list


def parse_item(text: str) -> Item:
    """An item from a command-line name: `Gui.Play`, `location:afk/spot` or `region:menus/bag`."""
    kind, _, name = text.partition(":")
    if name and kind in KINDS:
        return Item(name, kind)
    return Item(text)


@dataclass
class Result:
    image: Region | None = None
    region: Region | None = None
    point: Location | None = None
    region_name: str = ""  # the shared region target the image is searched in, by name, instead of its own box


def distinct(image: np.ndarray, shot: np.ndarray, box: Region) -> float:
    """The best score the image gets anywhere other than where it was taken: lower is safer."""
    result = matching.scores(image, shot)
    if result is None:
        return 0.0
    h, w = image.shape[:2]
    result[max(0, box.y - h + 1) : box.y + h, max(0, box.x - w + 1) : box.x + w] = -1
    return float(result.max()) if result.size else 0.0


def read_list(path: Path) -> list[Item]:
    """Targets from a list file: one per line, `name`, `location: name` or `region: name`, a note after `#`.

    A `[Screen name]` line starts a group of targets on the same screen. Blank lines
    and lines starting with `#` are skipped.
    """
    items = []
    screen = ""
    for line in path.read_text(encoding="utf-8").splitlines():
        text, _, note = line.partition("#")
        text = text.strip()
        if not text:
            continue
        if text.startswith("[") and text.endswith("]"):
            screen = text[1:-1].strip()
            continue
        kind, _, name = text.partition(":")
        if name and kind.strip() in KINDS:
            items.append(Item(name.strip(), kind.strip(), note.strip(), screen))
        else:
            items.append(Item(text, "image", note.strip(), screen))
    return items


def add_to_list(path: Path, item: Item) -> None:
    """Add a target to a list file: at the end of its screen's group, or at the end of the file."""
    text = item.name if item.kind == "image" else f"{item.kind}: {item.name}"
    line = f"{text:<40}  # {item.note}" if item.note else text
    lines = path.read_text(encoding="utf-8").splitlines() if path.is_file() else []
    at = len(lines)
    if item.screen:
        header = f"[{item.screen}]"
        starts = [i for i, x in enumerate(lines) if x.strip() == header]
        if starts:
            at = starts[0] + 1
            while at < len(lines) and lines[at].strip() and not lines[at].strip().startswith("["):
                at += 1
        else:
            lines += ["", header]
            at = len(lines)
    lines.insert(at, line)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def captured(item: Item, folder: Path) -> bool:
    """Whether a target is already saved in `folder`."""
    from ..core.targets import find_file

    if item.kind == "image":
        return find_file(item.name, [folder]) is not None
    return (folder / (item.name + ".json")).is_file()
