"""The test bench: darbit's own search, run on saved screens whose answers are known, for accuracy and speed.

    uv run python bench/run.py                     # bench/cases, and bench/private if it's there
    uv run python bench/run.py path/to/cases       # other cases
    uv run python bench/run.py --options fast,colour   # with matching options on (core/matching.py)

A case is a folder with `case.toml`: the screen, the folder of its targets, the display scaling it was taken at
(`scale`, 1.0 if left out) and what each target should give: `at = [x, y, w, h]`, or `absent = true`. A find
with `option = "..."` only counts when that option is on. Each search goes through `d.exists`, with the screen
grab and the scaling taken from the case, so it measures what a bot gets. Exits 1 if any answer is wrong.
"""

import argparse
import json
import statistics
import sys
import time
import tomllib
from dataclasses import asdict, dataclass
from pathlib import Path

import cv2
import numpy as np

from darbit.core.geometry import Region
from darbit.core.targets import load
from darbit.platform import screen
from darbit.runtime import find
from darbit.settings import settings

HERE = Path(__file__).parent
GOAL_IN_REGION = 10.0  # ms for one search inside a region (rebuild plan, section 9)
GOAL_WHOLE_SCREEN = 40.0  # ms for one search of the whole screen
OVERLAP = 0.5  # share of the expected box a match must cover (intersection over union) to be right


@dataclass
class Result:
    case: str
    target: str
    answer: str  # right, missed, false match, wrong place, or "needs <option>"
    score: float | None
    median_ms: float
    worst_ms: float
    goal_ms: float
    in_region: bool


def overlap(a: list[int], b: list[int]) -> float:
    ax, ay, aw, ah = a
    bx, by, bw, bh = b
    width = max(0, min(ax + aw, bx + bw) - max(ax, bx))
    height = max(0, min(ay + ah, by + bh) - max(ay, by))
    shared = width * height
    union = aw * ah + bw * bh - shared
    return shared / union if union else 0.0


def use_case_screen(pixels: np.ndarray, scale: float) -> None:
    """Make darbit's screen grabs and scaling come from the case instead of the real screen."""
    whole = Region(0, 0, pixels.shape[1], pixels.shape[0])

    def grab(region: Region | None = None) -> tuple[np.ndarray, Region]:
        area = whole if region is None else region.intersect(whole)
        if area is None:
            return np.zeros((0, 0, 3), np.uint8), Region(0, 0, 0, 0)
        part = pixels[area.y : area.y + area.h, area.x : area.x + area.w]
        return np.ascontiguousarray(part), area

    def scale_at(x: int, y: int) -> float:
        return scale

    screen.grab = grab
    screen.scale_at = scale_at


def run_case(folder: Path, options: set[str], repeat: int) -> list[Result]:
    spec = tomllib.loads((folder / "case.toml").read_text(encoding="utf-8"))
    pixels = cv2.imread(str(folder / spec.get("screen", "screen.png")), cv2.IMREAD_COLOR)
    if pixels is None:
        raise SystemExit(f"{folder}: can't read its screen")
    use_case_screen(pixels, float(spec.get("scale", 1.0)))
    settings.images = [folder / spec.get("images", "images")]
    settings.match = {name: True for name in options}
    settings.log = False
    settings.window = None
    found_results = []
    for item in spec.get("find", []):
        name = item["target"]
        option = item.get("option")
        in_region = load(name, settings.images).region is not None
        goal = GOAL_IN_REGION if in_region else GOAL_WHOLE_SCREEN
        if option and option not in options:
            found_results.append(Result(folder.name, name, f"needs {option}", None, 0.0, 0.0, goal, in_region))
            continue
        times = []
        match = None
        for _ in range(repeat):
            started = time.perf_counter()
            match = find.exists(name)
            times.append((time.perf_counter() - started) * 1000)
        answer = judge(match, item)
        score = round(match.score, 3) if match is not None else None
        found_results.append(
            Result(folder.name, name, answer, score, statistics.median(times), max(times), goal, in_region)
        )
    return found_results


def judge(match: object, item: dict) -> str:
    expected = item.get("at")
    if match is None:
        return "missed" if expected else "right"
    if not expected:
        return "false match"
    box = [match.x, match.y, match.w, match.h]
    return "right" if overlap(box, expected) >= OVERLAP else "wrong place"


def cases_in(folders: list[Path]) -> list[Path]:
    found = []
    for folder in folders:
        for case in sorted(folder.rglob("case.toml")):
            found.append(case.parent)
    return found


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="darbit's test bench: accuracy and speed on saved screens.")
    parser.add_argument("folders", nargs="*", type=Path, help="folders of cases (default: bench/cases, bench/private)")
    parser.add_argument("--options", default="", help="matching options to turn on, comma separated")
    parser.add_argument("--repeat", type=int, default=15, help="searches per target, for the timing")
    parser.add_argument("--json", type=Path, help="also write the results here")
    args = parser.parse_args(argv)
    if not args.folders and not (HERE / "cases").is_dir():
        import make_cases  # bench/ is on the path when this file runs

        make_cases.main()
    folders = args.folders or [path for path in (HERE / "cases", HERE / "private") if path.is_dir()]
    options = {part.strip() for part in args.options.split(",") if part.strip()}

    results: list[Result] = []
    for case in cases_in(folders):
        results.extend(run_case(case, options, args.repeat))

    print(f"{'case':16} {'target':24} {'answer':14} {'score':>6} {'median':>8} {'worst':>8} {'goal':>6}")
    for result in results:
        score = "" if result.score is None else f"{result.score:.3f}"
        timing = "" if result.answer.startswith("needs") else f"{result.median_ms:7.1f}ms {result.worst_ms:7.1f}ms"
        print(f"{result.case:16} {result.target:24} {result.answer:14} {score:>6} {timing:18} {result.goal_ms:4.0f}ms")

    counted = [result for result in results if not result.answer.startswith("needs")]
    wrong = [result for result in counted if result.answer != "right"]
    slow = [result for result in counted if result.median_ms > result.goal_ms]
    print()
    print(f"{len(counted) - len(wrong)} of {len(counted)} right; {len(slow)} over their speed goal")
    if args.json:
        args.json.write_text(json.dumps([asdict(result) for result in results], indent=2), encoding="utf-8")
    return 1 if wrong else 0


if __name__ == "__main__":
    sys.exit(main())
