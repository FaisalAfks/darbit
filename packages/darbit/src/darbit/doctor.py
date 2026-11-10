"""darbit doctor: what would stop a bot before it starts, found in seconds.

Its darbit.toml reads, every target in its setup guide (Image, Region, Location) is taken, this display's scaling is
the one its images were taken at, its game window is open (when darbit.toml names one), and the screen isn't locked.
A bot icon darbit.toml names that can't be read adds a note: the Studio shows the bot's initials instead.
Each check says ok, a problem, or a note it couldn't look, what it found and how to fix it. See the rebuild plan.
"""

import json
from dataclasses import dataclass, field
from pathlib import Path
from xml.etree import ElementTree

import cv2
import numpy as np

from .capture.guide import GuideError, progress, steps
from .capture.guide import load as load_guide
from .platform import screen as display
from .platform import system, windows
from .platform.backend import NotSupported
from .project.manifest import Project, ProjectError, icon_path, load

GUIDE = "guide.toml"
MOST_SHOWN = 8  # targets not taken named in `found`; the rest are counted (`missing` has them all)
CAPTURE = "take them with Capture in darbit Studio (darbit app)"


@dataclass
class Check:
    name: str
    ok: bool | None  # None: couldn't look
    found: str
    fix: str = ""  # what to do about it; empty when nothing needs doing
    missing: list[str] = field(default_factory=list)  # targets not taken, for Capture to open on


def run(folder: Path) -> list[Check]:
    """Every check on the bot at `folder`, in order. Stops after the first when darbit.toml doesn't read."""
    try:
        project = load(folder)
    except (ProjectError, OSError) as error:
        return [Check("darbit.toml", False, str(error), "fix darbit.toml, then check again")]
    images = [folder / name for name in project.images]
    found = [Check("darbit.toml", True, f"{project.name} {project.version}")]
    found.append(_targets(folder, images))
    found.append(_scaling(images))
    found.append(_window(project.window))
    found.append(_screen())
    icon = _icon(project)
    if icon is not None:
        found.append(icon)
    return found


def _icon(project: Project) -> Check | None:
    """A note when the icon darbit.toml names can't be shown; None when it can, or when there's none."""
    path = icon_path(project)
    if path is None or _readable(path):
        return None
    if not path.is_file():
        return Check("icon", None, f"no {project.icon}: the Studio shows the bot's initials")
    return Check("icon", None, f"{project.icon} can't be read: the Studio shows the bot's initials")


def _readable(path: Path) -> bool:
    """Whether a .png or .svg file opens as one."""
    if not path.is_file():
        return False
    if path.suffix.lower() == ".svg":
        try:
            root = ElementTree.parse(path).getroot()
        except (ElementTree.ParseError, OSError):
            return False
        return root.tag.endswith("svg")  # "{http://www.w3.org/2000/svg}svg" with its namespace
    try:
        data = np.fromfile(str(path), dtype=np.uint8)  # imread can't open every Windows path
    except OSError:
        return False
    return cv2.imdecode(data, cv2.IMREAD_UNCHANGED) is not None


def _targets(folder: Path, images: list[Path]) -> Check:
    path = folder / GUIDE
    if not path.is_file():
        return Check("targets", None, f"no {GUIDE}: nothing to check them against")
    try:
        guide = load_guide(path)
    except GuideError as error:
        return Check("targets", False, str(error), f"fix {GUIDE}, then check again")
    done = progress(guide, images[0])
    if done.done == done.total:
        return Check("targets", True, f"all {done.total} taken")
    missing = []
    for step in steps(guide):
        saved = (images[0] / f"{step.name}.png").is_file() or (images[0] / f"{step.name}.json").is_file()
        if not saved and step.name not in missing:
            missing.append(step.name)
    shown = ", ".join(missing[:MOST_SHOWN])
    more = len(missing) - MOST_SHOWN
    if more > 0:
        shown += f" and {more} more"
    return Check("targets", False, f"{done.total - done.done} of {done.total} not taken: {shown}", CAPTURE, missing)


def _scaling(images: list[Path]) -> Check:
    taken = set()
    for folder in images:
        for path in folder.glob("*.json"):
            try:
                scale = json.loads(path.read_text(encoding="utf-8")).get("scale")
            except (OSError, ValueError, AttributeError):
                continue
            if isinstance(scale, (int, float)):
                taken.add(float(scale))
    if not taken:
        return Check("display scaling", None, "the images don't say what scaling they were taken at")
    try:
        area = display.desktop()
        now = display.scale_at(area.x + area.w // 2, area.y + area.h // 2)
    except NotSupported:
        return Check("display scaling", None, "can't read this display's scaling here")
    shown = ", ".join(f"{scale:.0%}" for scale in sorted(taken))
    if taken == {now}:
        return Check("display scaling", True, f"{now:.0%}, as the images were taken")
    return Check(
        "display scaling",
        False,
        f"this display is at {now:.0%}, the images were taken at {shown}: darbit resizes them",
        f"set the display back to {shown} for the best matches",
    )


def _window(name: str | None) -> Check:
    if not name:
        return Check("game window", None, "darbit.toml names none")
    try:
        found = windows.matching(name)
    except NotSupported:
        return Check("game window", None, "can't look for windows here")
    if found:
        return Check("game window", True, f"{name} is open")
    return Check("game window", False, f"no window called {name}", "open it first")


def _screen() -> Check:
    if system.screen_usable():
        return Check("screen", True, "unlocked")
    return Check("screen", False, "locked: a bot waits until it's back", "unlock it")


def report(checks: list[Check]) -> str:
    """The checks as text, one line each, and the fix on its own line under a problem."""
    lines = []
    for check in checks:
        mark = "ok" if check.ok else "--" if check.ok is None else "!!"
        lines.append(f"{mark}  {check.name}: {check.found}")
        if check.fix:
            lines.append(f"    fix: {check.fix}")
    return "\n".join(lines)
