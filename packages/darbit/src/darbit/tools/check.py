"""Library health: how well every target is found, and whether something else looks alike.

    python -m darbit.tools.check                       # every target in images/, against the live screen
    python -m darbit.tools.check --screens shots/      # against saved screenshots (.png), e.g. one per game screen
    python -m darbit.tools.check --folder images Gui.Play Play.Raid
    python -m darbit.tools.check --similarity 0.85              # the similarity the bot uses

Each target is scored inside its own search region and everywhere else on the screen:

    ok        found in its region, nothing else on screen comes close
    risky     found, but something else on screen scores almost as high: it could be clicked by mistake
    moved     not found in its region, but found somewhere else: its region needs updating
    not seen  not on any of the screens checked

With several screenshots, each target gets its best result over all of them. Results
are added to state/check.jsonl, so scores can be followed over time.
"""

import argparse
import json
import os
import sys
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path

import cv2
import numpy as np

from ..core import matching
from ..core.geometry import Region
from ..core.targets import IMAGE_TYPES, Target, load
from ..platform import screen
from ..settings import settings

MARGIN = 0.1  # "risky" when something else scores within this of the target's own score


@dataclass
class Result:
    name: str
    verdict: str  # ok, risky, moved, not seen
    score: float  # best score in its region (or anywhere, for moved)
    elsewhere: float  # best score outside the spot it was found at
    at: tuple[int, int] | None  # where it was found
    screen: str  # which screen it was found on


def _region_best(
    result: np.ndarray, origin: Region, area: Region | None, size: tuple[int, int]
) -> tuple[float, tuple[int, int]]:
    """The best score in a score map for positions where the whole image fits inside `area`."""
    h, w = size
    if area is not None:
        x0, y0 = max(0, area.x - origin.x), max(0, area.y - origin.y)
        x1 = min(result.shape[1], area.right - origin.x - w + 1)
        y1 = min(result.shape[0], area.bottom - origin.y - h + 1)
        if x1 <= x0 or y1 <= y0:
            return 0.0, (0, 0)
        result = result[y0:y1, x0:x1]
    else:
        x0 = y0 = 0
    _, score, _, (x, y) = cv2.minMaxLoc(result)
    return float(score), (origin.x + x0 + x, origin.y + y0 + y)


def _elsewhere(result: np.ndarray, origin: Region, at: tuple[int, int], size: tuple[int, int]) -> float:
    """The best score anywhere other than the spot at `at`."""
    h, w = size
    result = result.copy()
    x, y = at[0] - origin.x, at[1] - origin.y
    result[max(0, y - h + 1) : y + h, max(0, x - w + 1) : x + w] = -1
    return float(result.max()) if result.size else 0.0


def check_one(target: Target, pixels: np.ndarray, origin: Region, screen_name: str) -> Result:
    """One target against one screen. The whole screen is scored once; its region and the rest come from that."""
    similarity = target.similarity if target.similarity is not None else settings.similarity
    result = matching.scores(target.pixels, pixels)
    if result is None:
        return Result(target.label, "not seen", 0.0, 0.0, None, screen_name)
    size = target.pixels.shape[:2]
    score, at = _region_best(result, origin, target.region, size)
    if score >= similarity:
        elsewhere = _elsewhere(result, origin, at, size)
        verdict = "risky" if elsewhere >= min(similarity, score - MARGIN) else "ok"
        return Result(target.label, verdict, round(score, 3), round(elsewhere, 3), at, screen_name)
    anywhere, where = _region_best(result, origin, None, size)
    if target.region is not None and anywhere >= similarity:
        return Result(target.label, "moved", round(anywhere, 3), round(score, 3), where, screen_name)
    return Result(target.label, "not seen", round(score, 3), round(anywhere, 3), None, screen_name)


RANK = {"ok": 0, "risky": 1, "moved": 2, "not seen": 3}


def _check_target(target: Target, screens: list[tuple[str, np.ndarray, Region]]) -> Result:
    tries = [check_one(target, pixels, origin, name) for name, pixels, origin in screens]
    return min(tries, key=_best_first)


def _best_first(result: Result) -> tuple[int, float]:
    """Sort key: the best verdict first, then the highest score."""
    return RANK[result.verdict], -result.score


def _by_verdict(result: Result) -> tuple[int, str]:
    """Sort key: worst verdicts last, by name within each."""
    return RANK[result.verdict], result.name


def check(targets: list[Target], screens: list[tuple[str, np.ndarray, Region]]) -> list[Result]:
    """Every target against every screen, in parallel (OpenCV works outside Python's lock); each target keeps
    its best result."""
    with ThreadPoolExecutor(max_workers=os.cpu_count() or 4) as pool:
        return list(pool.map(_check_target, targets, [screens] * len(targets)))


def _targets(folder: Path, names: list[str]) -> list[Target]:
    if not names:
        names = sorted({p.name for p in folder.iterdir() if p.suffix.lower() in IMAGE_TYPES})
    return [load(name, [folder]) for name in names]


def _screens(folder: Path | None) -> list[tuple[str, np.ndarray, Region]]:
    if folder is None:
        pixels, origin = screen.grab()
        return [("live screen", pixels, origin)]
    shots = []
    for path in sorted([*folder.glob("*.png"), *folder.glob("*.jpg")]):
        pixels = cv2.imdecode(np.fromfile(str(path), dtype=np.uint8), cv2.IMREAD_COLOR)
        if pixels is not None:
            shots.append((path.name, pixels, Region(0, 0, pixels.shape[1], pixels.shape[0])))
    return shots


def report(results: list[Result]) -> str:
    width = max([len(r.name) for r in results] + [6])
    lines = [f"{'target':<{width}}  verdict    score  elsewhere  screen"]
    for r in sorted(results, key=_by_verdict):
        lines.append(f"{r.name:<{width}}  {r.verdict:<9}  {r.score:5.2f}  {r.elsewhere:9.2f}  {r.screen}")
    counts = {v: sum(r.verdict == v for r in results) for v in RANK}
    lines.append(", ".join(f"{n} {v}" for v, n in counts.items() if n))
    return "\n".join(lines)


def taken_at_another_scaling(targets: list[Target], scale: float) -> str:
    """A line naming the targets taken at another display scaling than `scale`; empty when there are none."""
    others = []
    for target in targets:
        if target.scale is not None and abs(target.scale - scale) > 0.01:
            others.append(f"{target.name} ({target.scale:.0%})")
    if not others:
        return ""
    return f"taken at another scaling than this screen's {scale:.0%}, resized when searched: {', '.join(others)}"


def remember(results: list[Result], folder: Path) -> None:
    """Add the results to the check history."""
    folder.mkdir(parents=True, exist_ok=True)
    when = datetime.now(UTC).isoformat(timespec="seconds")
    with (folder / "check.jsonl").open("a", encoding="utf-8") as file:
        for r in results:
            file.write(json.dumps({"when": when, **asdict(r)}) + "\n")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m darbit.tools.check", description="Check every target's health.")
    parser.add_argument("names", nargs="*", help="targets to check (default: every image in the folder)")
    parser.add_argument("--folder", default="images", help="the targets' folder (default: images)")
    parser.add_argument("--screens", help="a folder of saved screenshots to check against, instead of the live screen")
    parser.add_argument("--similarity", type=float, help="similarity for targets without their own (default: settings)")
    parser.add_argument("--no-history", action="store_true", help="don't add the results to state/check.jsonl")
    args = parser.parse_args(argv)
    screen.enable_dpi_awareness()
    if args.similarity is not None:
        settings.similarity = args.similarity
    folder = Path(args.folder)
    screens = _screens(Path(args.screens) if args.screens else None)
    if not screens:
        print("no screenshots to check against")
        return 2
    targets = _targets(folder, args.names)
    results = check(targets, screens)
    print(report(results))
    others = taken_at_another_scaling(targets, screen.scale_at(0, 0))
    if others:
        print(others)
    if not args.no_history:
        remember(results, folder.parent / ".darbit" / "state")
    return 0 if all(r.verdict in ("ok", "not seen") for r in results) else 1


if __name__ == "__main__":
    sys.exit(main())
