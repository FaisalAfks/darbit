"""The Library page in darbit Studio: every asset a bot uses, where it's used, and renaming without breaking it.

An asset is a target in the bot's image folders: an image (`Lobby.Play.png` plus an optional `Lobby.Play.json`),
a region or a point (a `.json` alone). Pictures the setup guide asks for that aren't taken yet are listed as
missing. `uses` finds every line that names an asset, in the bot's Python files and its guide.toml. `rename`
changes the files and every one of those lines together, or nothing at all. Decision 0013, round 4.
"""

import base64
import json
import re
from dataclasses import dataclass
from pathlib import Path

import cv2
import numpy as np

from .. import paths
from ..project.manifest import Project

THUMB = 160  # px, the longer side of a card's thumbnail
HISTORY = 14  # last scores kept per asset for its small chart
SKIP_DIRS = {".venv", "venv", ".darbit", ".git", "node_modules", "__pycache__", "build", "dist"}
NAME = re.compile(r"^[A-Za-z][A-Za-z0-9_.\-]*$")


class LibraryError(ValueError):
    """A rename that can't be done; the message says why."""


@dataclass
class Use:
    file: Path
    line: int  # from 1
    text: str


def _folders(project: Project) -> list[Path]:
    found = []
    for name in project.images or ["images"]:
        folder = project.folder / name
        if folder.is_dir():
            found.append(folder)
    return found


def _thumbnail(path: Path) -> tuple[str | None, list[int] | None]:
    pixels = cv2.imdecode(np.fromfile(str(path), dtype=np.uint8), cv2.IMREAD_COLOR)
    if pixels is None:
        return None, None
    height, width = pixels.shape[:2]
    biggest = max(width, height)
    if biggest > THUMB:
        factor = THUMB / biggest
        pixels = cv2.resize(
            pixels, (max(1, round(width * factor)), max(1, round(height * factor))), interpolation=cv2.INTER_AREA
        )
    ok, data = cv2.imencode(".png", pixels)
    if not ok:
        return None, [width, height]
    return "data:image/png;base64," + base64.b64encode(data.tobytes()).decode("ascii"), [width, height]


def _settings(path: Path) -> dict:
    if not path.is_file():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    if isinstance(data, dict):
        return data
    return {}


def _scores(project: Project) -> dict[str, list[float]]:
    """Each asset's scores from `darbit check`, oldest first, the last few kept."""
    history = paths.project_dir(project.folder) / "state" / "check.jsonl"
    found: dict[str, list[float]] = {}
    if not history.is_file():
        return found
    for line in history.read_text(encoding="utf-8").splitlines():
        try:
            entry = json.loads(line)
        except ValueError:
            continue
        if not isinstance(entry, dict) or not isinstance(entry.get("score"), (int, float)):
            continue
        name = str(entry.get("name", "")).removesuffix(".png")
        found.setdefault(name, []).append(float(entry["score"]))
    for name, scores in found.items():
        found[name] = scores[-HISTORY:]
    return found


def group_of(name: str) -> str:
    """The screen an asset belongs to, from its name: "Lobby.Play" -> "Lobby"."""
    if "." in name:
        return name.split(".")[0]
    return "Other"


def assets(project: Project) -> list[dict]:
    """Every asset: images, regions, points, and the guide's pictures still missing."""
    scores = _scores(project)
    found: dict[str, dict] = {}
    for folder in _folders(project):
        for path in sorted(folder.iterdir()):
            if path.suffix.lower() == ".png":
                name = path.stem
                settings = _settings(path.with_suffix(".json"))
                thumbnail, size = _thumbnail(path)
                found[name] = {
                    "name": name,
                    "kind": "image",
                    "group": group_of(name),
                    "thumbnail": thumbnail,
                    "size": size,
                    "region": settings.get("region"),
                    "similarity": settings.get("similarity"),
                    "scores": scores.get(name, []),
                    "missing": False,
                }
        for path in sorted(folder.glob("*.json")):
            name = path.stem
            if name in found:
                continue
            settings = _settings(path)
            kind = "point"
            if settings.get("region") and not settings.get("location"):
                kind = "region"
            found[name] = {
                "name": name,
                "kind": kind,
                "group": group_of(name),
                "thumbnail": None,
                "size": None,
                "region": settings.get("region"),
                "location": settings.get("location"),
                "similarity": None,
                "scores": [],
                "missing": False,
            }
    for name, kind in _guide_items(project):
        if name not in found:
            found[name] = {
                "name": name,
                "kind": kind,
                "group": group_of(name),
                "thumbnail": None,
                "size": None,
                "scores": [],
                "missing": True,
            }
    counts = _use_counts(project, list(found))
    result = []
    for name in sorted(found):
        entry = found[name]
        entry["uses"] = counts.get(name, 0)
        result.append(entry)
    return result


def _guide_items(project: Project) -> list[tuple[str, str]]:
    guide_file = project.folder / "guide.toml"
    if not guide_file.is_file():
        return []
    from ..capture.guide import GuideError, load, steps

    try:
        guide = load(guide_file)
    except GuideError:
        return []
    found = []
    for step in steps(guide):
        kind = step.kind
        if kind == "location":
            kind = "point"
        found.append((step.name, kind))
    return found


def _pattern(name: str) -> re.Pattern:
    """`name` as a whole asset name: not part of a longer name, though `.png` or `.json` may follow."""
    return re.compile(r"(?<![\w])" + re.escape(name) + r"(?![\w])(?!\.(?!png\b|json\b)\w)")


def _source_files(project: Project) -> list[Path]:
    found = []
    for path in project.folder.rglob("*"):
        if not path.is_file():
            continue
        if _skipped(path.relative_to(project.folder)):
            continue
        if path.suffix == ".py" or path.name == "guide.toml":
            found.append(path)
    return found


def _skipped(relative: Path) -> bool:
    """Whether a file sits in a folder that isn't the bot's own code (an environment, logs, git)."""
    for part in relative.parts[:-1]:
        if part in SKIP_DIRS or part.startswith("."):
            return True
    return False


def _read(path: Path) -> str:
    """A text file exactly as it is, line endings included."""
    return path.read_bytes().decode("utf-8")


def uses(project: Project, name: str) -> list[Use]:
    """Every line in the bot's code and guide that names this asset."""
    pattern = _pattern(name)
    found = []
    for path in _source_files(project):
        try:
            lines = _read(path).splitlines()
        except (OSError, UnicodeDecodeError):
            continue
        for number, line in enumerate(lines, start=1):
            if pattern.search(line):
                found.append(Use(path, number, line.strip()))
    return found


def _use_counts(project: Project, names: list[str]) -> dict[str, int]:
    counts: dict[str, int] = {}
    texts = []
    for path in _source_files(project):
        try:
            texts.append(_read(path))
        except (OSError, UnicodeDecodeError):
            continue
    for name in names:
        pattern = _pattern(name)
        total = 0
        for text in texts:
            total += len(pattern.findall(text))
        counts[name] = total
    return counts


def _asset_files(project: Project, name: str) -> list[Path]:
    found = []
    for folder in _folders(project):
        for suffix in (".png", ".json"):
            path = folder / (name + suffix)
            if path.is_file():
                found.append(path)
    return found


def rename_plan(project: Project, old: str, new: str) -> dict:
    """What a rename would change: the asset's files and every line naming it. Changes nothing."""
    if not NAME.match(new):
        raise LibraryError(f"{new!r} isn't a name: start with a letter; use letters, digits, '.', '_' or '-'")
    if new == old:
        raise LibraryError("that's the same name")
    files = _asset_files(project, old)
    if not files:
        raise LibraryError(f"no asset called {old}")
    if _asset_files(project, new):
        raise LibraryError(f"there's already an asset called {new}")
    pattern = _pattern(old)
    lines = []
    for use in uses(project, old):
        after = pattern.sub(new, use.text)
        lines.append(
            {
                "file": use.file.relative_to(project.folder).as_posix(),
                "line": use.line,
                "before": use.text,
                "after": after,
            }
        )
    renames = []
    for path in files:
        renames.append({"from": path.name, "to": new + path.suffix})
    return {"old": old, "new": new, "files": renames, "lines": lines}


def rename(project: Project, old: str, new: str) -> dict:
    """Rename an asset and every line that names it, all together; if anything fails, nothing changes."""
    plan = rename_plan(project, old, new)
    pattern = _pattern(old)
    originals: dict[Path, str] = {}
    for use in uses(project, old):
        if use.file not in originals:
            originals[use.file] = _read(use.file)
    moved: list[tuple[Path, Path]] = []
    written: list[Path] = []
    try:
        for path, text in originals.items():
            path.write_bytes(pattern.sub(new, text).encode("utf-8"))
            written.append(path)
        for path in _asset_files(project, old):
            target = path.with_name(new + path.suffix)
            path.rename(target)
            moved.append((path, target))
    except OSError as error:
        for path in written:
            path.write_bytes(originals[path].encode("utf-8"))
        for before, after in moved:
            after.rename(before)
        raise LibraryError(f"couldn't rename {old}: {error}; nothing was changed") from error
    return plan


SCREEN_WIDTH = 1280  # px, the kept screen shots are sent at most this wide


def screens(project: Project) -> list[dict]:
    """Each screen's last shot (from Capture) with the assets placed on it, for the Library's Screen view."""
    from ..capture.service import screens_folder

    folder = screens_folder(project.folder)
    if not folder.is_dir():
        return []
    found = []
    for path in sorted(folder.glob("*.jpg")):
        places = _settings(path.with_suffix(".json"))
        pixels = cv2.imdecode(np.fromfile(str(path), dtype=np.uint8), cv2.IMREAD_COLOR)
        if pixels is None:
            continue
        height, width = pixels.shape[:2]
        if width > SCREEN_WIDTH:
            pixels = cv2.resize(
                pixels, (SCREEN_WIDTH, round(height * SCREEN_WIDTH / width)), interpolation=cv2.INTER_AREA
            )
        ok, data = cv2.imencode(".jpg", pixels, [cv2.IMWRITE_JPEG_QUALITY, 80])
        if not ok:
            continue
        picture = "data:image/jpeg;base64," + base64.b64encode(data.tobytes()).decode("ascii")
        found.append(
            {"screen": path.stem, "picture": picture, "w": width, "h": height, "assets": places.get("assets", {})}
        )
    return found
