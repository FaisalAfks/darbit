"""Targets: what to look for or point at. An image, a location, or both.

A target saved by the capture tool is two files with the same name:
`lobby/play.png` (the image) and `lobby/play.json` (its settings):

    {"kind": "image", "region": [x, y, w, h], "similarity": 0.85, "offset": [dx, dy],
     "location": [x, y], "scale": 1.5, "window": [w, h], "origin": [x, y]}

`region` is a box, or the name of a region target in the same folder ("Bag.List"): images that are searched in the
same place share one, and moving it moves them all. `kind` says what the target is: an image (searched in its region, the whole screen without one, and clicked at its
centre moved by `offset`), a region, or a location. Files from before it say nothing; `kind_of` works it out from what
they have. Every other field is optional.
`window` and `origin` are the size and top-left corner of the app window it was taken in;
with them, core/placement.py follows the window when it moves or changes size.

A Pattern is a target by name with some settings changed in code. Loaded targets are kept in memory and
their files checked at most once a second, so a picture taken again is used from the next search on.
"""

import json
import time
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
    origin: tuple[int, int] | None = None  # that window's top-left corner on screen, when captured
    match: dict | None = None  # matching options for this target (core/matching.py), over settings.match
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


EXACT = 0.99  # Pattern.exact()


@dataclass(frozen=True)
class Pattern:
    """A picture by name with settings changed in code: `Pattern("Lobby.Play").similar(0.85).offset(10, 0)`.
    The picture's .json applies first, these on top."""

    image: str | Path
    similarity: float | None = None
    click_offset: tuple[float, float] | None = None
    region: Region | None = None
    match: dict | None = None

    def similar(self, similarity: float) -> "Pattern":
        """The lowest score that counts as found, 0 to 1."""
        return replace(self, similarity=similarity)

    def exact(self) -> "Pattern":
        return replace(self, similarity=EXACT)

    def offset(self, dx: float, dy: float) -> "Pattern":
        """Click this far from the picture's centre."""
        return replace(self, click_offset=(dx, dy))

    def within(self, region: Region) -> "Pattern":
        """Search only here."""
        return replace(self, region=region)

    def options(self, **values: object) -> "Pattern":
        """Matching options on top of the picture's own: `.options(fast=True, colour=True)`."""
        merged = dict(self.match or {})
        merged.update(values)
        return replace(self, match=merged)

    @property
    def label(self) -> str:
        return str(self.image)


_images: dict[Path, tuple[float, np.ndarray]] = {}  # per file: its modified time and its pixels


def read_image(path: Path) -> np.ndarray:
    """An image file as BGR pixels, cached until the file changes."""
    modified = path.stat().st_mtime
    cached = _images.get(path)
    if cached is not None and cached[0] == modified:
        return cached[1]
    pixels = cv2.imdecode(np.fromfile(str(path), dtype=np.uint8), cv2.IMREAD_COLOR)
    if pixels is None:
        raise TargetError(f"can't read the image {path}")
    _images[path] = (modified, pixels)
    return pixels


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


KINDS = ("image", "region", "location")


def kind_of(settings: dict, has_image: bool) -> str:
    """What a target is: the kind its settings file names, else worked out from what it has (an image; a region
    without a location; else a location)."""
    named = settings.get("kind")
    if named in KINDS:
        return named
    if has_image:
        return "image"
    if settings.get("region") and not settings.get("location"):
        return "region"
    return "location"


def shared_region(name: str, folder: Path) -> list | None:
    """The box of the region target called `name` in `folder`, for the images that name it; None if there's none."""
    path = folder / (name + ".json")
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    region = data.get("region") if isinstance(data, dict) else None
    if isinstance(region, list) and len(region) == 4:
        return region
    return None


def _from_json(target: Target, path: Path) -> Target:
    data = json.loads(path.read_text(encoding="utf-8"))
    changes: dict = {}
    region = data.get("region")
    if isinstance(region, str):
        region = shared_region(region, path.parent)
        if region is None:
            raise TargetError(f"{path.name} names the region {data['region']!r}, and there's no region by that name")
    if region is not None:
        changes["region"] = Region(*region)
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
    if "origin" in data:
        changes["origin"] = tuple(data["origin"])
    if isinstance(data.get("match"), dict):
        changes["match"] = data["match"]
    return replace(target, **changes)


CHECK_EVERY = 1.0  # seconds between checks that a loaded target's files haven't changed


@dataclass
class _Loaded:
    checked: float
    files: tuple
    target: Target


_loaded: dict[tuple[str, tuple[Path, ...]], _Loaded] = {}


def load(what: str | Path | Target | Pattern, folders: list[Path]) -> Target:
    """A ready target from a name, a file, a Pattern or a Target: its image read and its settings file applied."""
    if isinstance(what, Pattern):
        return _changed(load(what.image, folders), what)
    if isinstance(what, Target):
        return _load(what, folders)
    key = (str(what), tuple(folders))
    now = time.monotonic()
    kept = _loaded.get(key)
    if kept is not None and now - kept.checked < CHECK_EVERY:
        return kept.target
    files = _files(what, folders)
    if kept is not None and kept.files == files:
        kept.checked = now
        return kept.target
    target = _load(Target(image=what), folders)
    _loaded[key] = _Loaded(now, files, target)
    return target


def forget() -> None:
    """Drop every loaded target, so the next search reads the files again."""
    _loaded.clear()


def _files(name: str | Path, folders: list[Path]) -> tuple:
    """The target's image and settings files with their modified times: when these change, it's loaded again."""
    stamps = []
    for path in (find_file(name, folders), _settings_file(name, folders)):
        if path is None:
            stamps.append(None)
        else:
            stamps.append((path, path.stat().st_mtime))
    return tuple(stamps)


def _changed(target: Target, pattern: Pattern) -> Target:
    """A loaded target with a Pattern's settings on top."""
    changes: dict = {}
    if pattern.similarity is not None:
        changes["similarity"] = pattern.similarity
    if pattern.click_offset is not None:
        changes["offset"] = pattern.click_offset
    if pattern.region is not None:
        changes["region"] = pattern.region
    if pattern.match:
        merged = dict(target.match or {})
        merged.update(pattern.match)
        changes["match"] = merged
    return replace(target, **changes)


def _load(target: Target, folders: list[Path]) -> Target:
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
        if target.location is not None or target.region is not None:  # a point or an area, no image
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
        _with(path, ".json").write_text(json.dumps(clean, indent=2) + "\n", encoding="utf-8", newline="\n")
    forget()
