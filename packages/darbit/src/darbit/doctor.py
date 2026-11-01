"""darbit doctor: what would stop a bot before it starts, found in seconds.

Its darbit.toml reads, every picture in its setup guide is taken, this display's scaling is the one its pictures
were taken at, its game window is open (when darbit.toml names one), and the screen isn't locked. Each check says
ok, a problem, or a note it couldn't look (on a system without that piece). See the rebuild plan, section 13.
"""

import json
from dataclasses import dataclass
from pathlib import Path

from .capture.guide import GuideError, progress, steps
from .capture.guide import load as load_guide
from .platform import screen as display
from .platform import system, windows
from .platform.backend import NotSupported
from .project.manifest import ProjectError, load

GUIDE = "guide.toml"
MOST_MISSING = 8  # missing pictures named; the rest are counted


@dataclass
class Check:
    name: str
    ok: bool | None  # None: couldn't look
    say: str


def run(folder: Path) -> list[Check]:
    """Every check on the bot at `folder`, in order. Stops after the first when darbit.toml doesn't read."""
    try:
        project = load(folder)
    except (ProjectError, OSError) as error:
        return [Check("darbit.toml", False, str(error))]
    images = [folder / name for name in project.images]
    found = [Check("darbit.toml", True, f"{project.name} {project.version}")]
    found.append(_pictures(folder, images))
    found.append(_scaling(images))
    found.append(_window(project.window))
    found.append(_screen())
    return found


def _pictures(folder: Path, images: list[Path]) -> Check:
    path = folder / GUIDE
    if not path.is_file():
        return Check("pictures", None, f"no {GUIDE}: nothing to check them against")
    try:
        guide = load_guide(path)
    except GuideError as error:
        return Check("pictures", False, str(error))
    done = progress(guide, images[0])
    if done.done == done.total:
        return Check("pictures", True, f"all {done.total} taken")
    missing = []
    for step in steps(guide):
        saved = (images[0] / f"{step.name}.png").is_file() or (images[0] / f"{step.name}.json").is_file()
        if not saved and step.name not in missing:
            missing.append(step.name)
    shown = ", ".join(missing[:MOST_MISSING])
    more = len(missing) - MOST_MISSING
    if more > 0:
        shown += f" and {more} more"
    return Check("pictures", False, f"{done.total - done.done} of {done.total} not taken: {shown} (darbit guide)")


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
        return Check("display scaling", None, "the pictures don't say what they were taken at")
    try:
        area = display.desktop()
        now = display.scale_at(area.x + area.w // 2, area.y + area.h // 2)
    except NotSupported:
        return Check("display scaling", None, "can't read this display's scaling here")
    shown = ", ".join(f"{scale:.0%}" for scale in sorted(taken))
    if taken == {now}:
        return Check("display scaling", True, f"{now:.0%}, as the pictures were taken")
    return Check(
        "display scaling",
        False,
        f"this display is at {now:.0%}, the pictures were taken at {shown}: darbit resizes them, "
        "but set it back for the best matches",
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
    return Check("game window", False, f"no window called {name}: open it first")


def _screen() -> Check:
    if system.screen_usable():
        return Check("screen", True, "unlocked")
    return Check("screen", False, "locked: a bot waits until it's back")


def report(checks: list[Check]) -> str:
    lines = []
    for check in checks:
        mark = "ok" if check.ok else "--" if check.ok is None else "!!"
        lines.append(f"{mark}  {check.name}: {check.say}")
    return "\n".join(lines)
