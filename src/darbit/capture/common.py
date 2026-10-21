"""What the capture screens share: items, results, the look, and small drawing helpers."""
from __future__ import annotations

import base64
import re
import tkinter as tk
import tokenize
from dataclasses import dataclass, field
from pathlib import Path
from typing import ClassVar

import cv2
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

    @staticmethod
    def parse(text: str) -> Item:
        kind, _, name = text.partition(":")
        if name and kind in KINDS:
            return Item(name, kind)
        return Item(text)


@dataclass
class Result:
    image: Region | None = None
    region: Region | None = None
    point: Location | None = None


class Theme:
    KEY = "#ff00fe"  # drawn as transparent, for rounded corners
    CARD = "#17181d"
    RAISED = "#22242b"
    LINE = "#2c2f38"
    TEXT = "#eef0f4"
    MUTED = "#8b8f9a"
    ACCENT = "#5ac8fa"
    ACCENT2 = "#a78bfa"
    OK = "#4ade80"
    WARN = "#fbbf24"
    DANGER = "#f87171"
    FONT = "Segoe UI"
    BOLD = "Segoe UI Semibold"
    MONO = "Consolas"
    KIND_COLOR: ClassVar[dict[str, str]] = {"image": ACCENT, "location": OK, "region": ACCENT2}
    KIND_GLYPH: ClassVar[dict[str, str]] = {"image": "▣", "location": "◎", "region": "⬚"}


def photo(pixels: np.ndarray) -> tk.PhotoImage:
    _, data = cv2.imencode(".png", pixels)
    return tk.PhotoImage(data=base64.b64encode(data.tobytes()))


def rounded(canvas: tk.Canvas, x0: float, y0: float, x1: float, y1: float, r: float, **options) -> int:
    """A rounded rectangle on a canvas."""
    r = min(r, (x1 - x0) / 2, (y1 - y0) / 2)
    points = [x0 + r, y0, x1 - r, y0, x1, y0, x1, y0 + r, x1, y1 - r, x1, y1, x1 - r, y1,
              x0 + r, y1, x0, y1, x0, y1 - r, x0, y0 + r, x0, y0]
    return canvas.create_polygon(points, smooth=True, **options)


def blend(a: str, b: str, t: float) -> str:
    """The colour `t` of the way from a to b."""
    ca = [int(a[i : i + 2], 16) for i in (1, 3, 5)]
    cb = [int(b[i : i + 2], 16) for i in (1, 3, 5)]
    return "#" + "".join(f"{round(x + (y - x) * t):02x}" for x, y in zip(ca, cb, strict=True))


def gradient(canvas: tk.Canvas, x0: int, y0: int, x1: int, y1: int, a: str, b: str, **options) -> None:
    """A left-to-right gradient bar."""
    width = max(1, x1 - x0)
    for i in range(0, width, 2):
        canvas.create_rectangle(x0 + i, y0, x0 + i + 2, y1, fill=blend(a, b, i / width), width=0, **options)


def distinct(image: np.ndarray, shot: np.ndarray, box: Region) -> float:
    """The best score the image gets anywhere other than where it was taken: lower is safer."""
    result = matching.scores(image, shot)
    if result is None:
        return 0.0
    h, w = image.shape[:2]
    result[max(0, box.y - h + 1) : box.y + h, max(0, box.x - w + 1) : box.x + w] = -1
    return float(result.max()) if result.size else 0.0


def images_in(script: Path) -> list[str]:
    """Every image name written in a script (strings ending in .png, comments ignored), in order."""
    names: list[str] = []
    with script.open(encoding="utf-8") as file:
        for token in tokenize.generate_tokens(file.readline):
            if token.type == tokenize.STRING:
                for name in re.findall(r"[^\"']+\.png", token.string):
                    if name not in names:
                        names.append(name)
    return names


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
