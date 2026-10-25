"""Targets: what to look for or point at. An image, a location, or both.

A target saved by the capture tool is two files with the same name:
`lobby/play.png` (the image) and `lobby/play.json` (its settings):

    {"region": [x, y, w, h], "similarity": 0.85, "offset": [dx, dy],
     "location": [x, y], "scale": 1.5, "window": [w, h]}

Every field is optional. A target with only a location and no image is a point.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field, replace
from pathlib import Path

import cv2
import numpy as np

from ..errors import TargetError
from .geometry import Location, Region


@dataclass(frozen=True)
class Target:
    """What to find. `Target("Gui.Play.png", similarity=0.9)`, or loaded by name from the image folders."""

    image: str | Path | None = None
    similarity: float | None = None  # None: settings.similarity
    region: Region | None = None  # where to search; None: the whole screen
    offset: tuple[float, float] = (0, 0)  # click point, from the image's centre
    location: Location | None = None  # a fixed point, for targets without an image
    name: str = ""
    scale: float | None = None  # display scaling when captured
    window: tuple[int, int] | None = None  # size of the window it was captured in
    _pixels: np.ndarray | None = field(default=None, repr=False, compare=False)

    @property
    def pixels(self) -> np.ndarray:
        """The image as BGR pixels."""
        if self._pixels is None:
            raise TargetError(f"{self.label} has no image")
        return self._pixels

    @property
    def label(self) -> str:
        return self.name or str(self.image or self.location)


@dataclass(frozen=True)
class Match:
    """Where a target was found."""

    x: int
    y: int
    w: int
    h: int
    score: float
    target: Target

    @property
    def name(self) -> str:
        return self.target.name

    @property
    def region(self) -> Region:
        return Region(self.x, self.y, self.w, self.h)

    @property
    def center(self) -> Location:
        return self.region.center

    @property
    def point(self) -> Location:
        """Where a click on this match lands: the centre plus the target's offset."""
        return self.center.moved(*self.target.offset)


_cache: dict[tuple[Path, float], np.ndarray] = {}


def read_image(path: Path) -> np.ndarray:
    """An image file as BGR pixels, cached until the file changes."""
    key = (path, path.stat().st_mtime)
    if key not in _cache:
        pixels = cv2.imdecode(np.fromfile(str(path), dtype=np.uint8), cv2.IMREAD_COLOR)
        if pixels is None:
            raise TargetError(f"can't read the image {path}")
        _cache[key] = pixels
    return _cache[key]


IMAGE_TYPES = (".png", ".jpg", ".jpeg", ".bmp")


def _with(path: Path, suffix: str) -> Path:
    """`path` plus a suffix, keeping dots in the name: Gui.Play -> Gui.Play.png."""
    return path.with_name(path.name + suffix)


def _stem(name: str | Path) -> Path:
    """A name without its image suffix: Gui.Play.png -> Gui.Play."""
    path = Path(name)
    return path.with_suffix("") if path.suffix.lower() in IMAGE_TYPES else path


def _look(relative: list[Path], folders: list[Path]) -> Path | None:
    for candidate in relative:
        if candidate.is_absolute():
            if candidate.is_file():
                return candidate
            continue
        for folder in folders:
            if (folder / candidate).is_file():
                return folder / candidate
    return None


def find_file(name: str | Path, folders: list[Path]) -> Path | None:
    """The image file for a name, as given or with .png added, in each folder in turn."""
    path = Path(name)
    candidates = [path] if path.suffix.lower() in IMAGE_TYPES else [_with(path, ".png"), path]
    return _look(candidates, folders)


def _settings_file(name: str | Path, folders: list[Path]) -> Path | None:
    return _look([_with(_stem(name), ".json")], folders)


def _from_json(target: Target, path: Path) -> Target:
    data = json.loads(path.read_text(encoding="utf-8"))
    changes: dict = {}
    if "region" in data:
        changes["region"] = Region(*data["region"])
    if "similarity" in data and target.similarity is None:
        changes["similarity"] = float(data["similarity"])
    if "offset" in data:
        changes["offset"] = tuple(data["offset"])
    if "location" in data:
        changes["location"] = Location(*data["location"])
    if "scale" in data:
        changes["scale"] = float(data["scale"])
    if "window" in data:
        changes["window"] = tuple(data["window"])
    return replace(target, **changes)


def load(what: str | Path | Target, folders: list[Path]) -> Target:
    """A ready target from a name, a file or a Target: its image read and its settings file applied."""
    target = what if isinstance(what, Target) else Target(image=what)
    if target.image is None:
        if target.location is None:
            raise TargetError("a target needs an image or a location")
        return target
    name = target.name or str(target.image)
    settings_file = _settings_file(target.image, folders)
    if settings_file is not None:
        target = _from_json(target, settings_file)
    path = find_file(target.image, folders)
    if path is None:
        if target.location is not None:  # a point saved by the capture tool, no image
            return replace(target, name=name)
        raise TargetError(f"no image {target.image!r} in {', '.join(str(f) for f in folders)}")
    return replace(target, name=name, _pixels=read_image(path))


def save(path: Path, image: np.ndarray | None, **fields) -> None:
    """Save a target: `path` without a suffix, e.g. images/lobby/play. Fields go to the .json."""
    path.parent.mkdir(parents=True, exist_ok=True)
    if image is not None:
        ok, data = cv2.imencode(".png", image)
        if not ok:
            raise TargetError(f"can't encode the image for {path}")
        data.tofile(str(_with(path, ".png")))
    clean = {k: v for k, v in fields.items() if v is not None}
    if clean:
        _with(path, ".json").write_text(json.dumps(clean, indent=2) + "\n", encoding="utf-8")
