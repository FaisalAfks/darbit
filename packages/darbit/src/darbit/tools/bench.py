"""The test bench: darbit's own search on saved screens whose answers are known, for accuracy and speed.

    darbit bench bench/cases                            # every case.toml under the folders
    darbit bench cases --options fast,grayscale         # with matching options on (core/matching.py)
    darbit bench cases --baseline bench/baseline.json   # also fail when a search got much slower
    darbit bench --from-screens ../my-bot cases         # cases from the screens darbit Studio saved for a bot

A case is a folder with `case.toml`: the screen, the folder of its targets, the display scaling it was taken at
(`scale`, 1.0 if left out), where the app's window is (`window`, for window space) and what each target should
give: `at = [x, y, w, h]`, or `absent = true`. A find with `option = "..."` only counts when that option is on
(`"window|sizes"`: either). The option `window` is window space (settings.space), not a matching option. Each
search goes through `d.exists`, with the screen grab and the scaling taken from the case, so it measures what a bot
gets. Exits 1 when an answer is wrong, or when a search is over the baseline's speed by more than `--slower` times.
"""

import argparse
import json
import shutil
import statistics
import time
import tomllib
from dataclasses import asdict, dataclass
from pathlib import Path

GOAL_IN_REGION = 10.0  # ms for one search inside a region (rebuild plan, section 9)
GOAL_WHOLE_SCREEN = 40.0  # ms for one search of the whole screen
OVERLAP = 0.5  # share of the expected box a match must cover (intersection over union) to be right
SLOWER = 2.0  # how many times slower than its baseline a search may get before the bench fails
NOISE_MS = 3.0  # differences smaller than this are timer noise, never a slowdown


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

    @property
    def key(self) -> str:
        return f"{self.case}/{self.target}"

    @property
    def counted(self) -> bool:
        return not self.answer.startswith("needs")


def overlap(a: list[int], b: list[int]) -> float:
    """Intersection over union of two [x, y, w, h] boxes."""
    ax, ay, aw, ah = a
    bx, by, bw, bh = b
    width = max(0, min(ax + aw, bx + bw) - max(ax, bx))
    height = max(0, min(ay + ah, by + bh) - max(ay, by))
    shared = width * height
    union = aw * ah + bw * bh - shared
    return shared / union if union else 0.0


def judge(match: object, item: dict) -> str:
    """right, missed, false match or wrong place, for one search against what the case expects."""
    expected = item.get("at")
    if match is None:
        return "missed" if expected else "right"
    if not expected:
        return "false match"
    box = [match.x, match.y, match.w, match.h]
    return "right" if overlap(box, expected) >= OVERLAP else "wrong place"


def cases_in(folders: list[Path]) -> list[Path]:
    """Every folder with a case.toml under the folders, in order."""
    found = []
    for folder in folders:
        for case in sorted(folder.rglob("case.toml")):
            found.append(case.parent)
    return found


def _use_case_screen(pixels, scale: float) -> None:
    """Make darbit's screen grabs and scaling come from the case instead of the real screen."""
    import numpy as np

    from ..core.geometry import Region
    from ..platform import screen

    whole = Region(0, 0, pixels.shape[1], pixels.shape[0])

    def grab(region=None):
        area = whole if region is None else region.intersect(whole)
        if area is None:
            return np.zeros((0, 0, 3), np.uint8), Region(0, 0, 0, 0)
        part = pixels[area.y : area.y + area.h, area.x : area.x + area.w]
        return np.ascontiguousarray(part), area

    def scale_at(x: int, y: int) -> float:
        return scale

    screen.grab = grab
    screen.scale_at = scale_at


def _use_case_window(area: list[int] | None) -> None:
    """Make the app's window be where the case says (or not open), for window space."""
    from ..core.geometry import Region
    from ..platform.backend import Window
    from ..runtime import find

    def matching(name: str, loose: bool = False) -> list[Window]:
        return [Window(1, "Game", "game.exe", 1)] if area else []

    def region(handle: int) -> Region:
        return Region(*area)

    find.windows.matching = matching
    find.windows.region = region


def run_case(folder: Path, options: set[str], repeat: int) -> list[Result]:
    """Search every target of one case `repeat` times and judge the answer."""
    import cv2

    from ..core.targets import load
    from ..runtime import find
    from ..settings import settings

    spec = tomllib.loads((folder / "case.toml").read_text(encoding="utf-8"))
    pixels = cv2.imread(str(folder / spec.get("screen", "screen.png")), cv2.IMREAD_COLOR)
    if pixels is None:
        raise SystemExit(f"{folder}: can't read its screen")
    _use_case_screen(pixels, float(spec.get("scale", 1.0)))
    settings.images = [folder / spec.get("images", "images")]
    settings.match = {name: True for name in options if name != "window"}
    settings.log = False
    settings.space = "window" if "window" in options else "screen"
    settings.window = "Game" if spec.get("window") else None
    _use_case_window(spec.get("window"))
    results = []
    for item in spec.get("find", []):
        name = item["target"]
        option = item.get("option")
        in_region = load(name, settings.images).region is not None
        goal = GOAL_IN_REGION if in_region else GOAL_WHOLE_SCREEN
        if option and not options.intersection(option.split("|")):
            results.append(Result(folder.name, name, f"needs {option}", None, 0.0, 0.0, goal, in_region))
            continue
        times = []
        match = None
        for _ in range(repeat):
            started = time.perf_counter()
            match = find.exists(name)
            times.append((time.perf_counter() - started) * 1000)
        score = round(match.score, 3) if match is not None else None
        results.append(
            Result(folder.name, name, judge(match, item), score, statistics.median(times), max(times), goal, in_region)
        )
    return results


def slower_than(results: list[Result], baseline: dict[str, float], times: float = SLOWER) -> list[str]:
    """The searches that took more than `times` their baseline (and more than timer noise), as sentences."""
    slow = []
    for result in results:
        before = baseline.get(result.key)
        if not result.counted or before is None:
            continue
        if result.median_ms > before * times and result.median_ms - before > NOISE_MS:
            slow.append(f"{result.key}: {result.median_ms:.1f} ms, was {before:.1f} ms")
    return slow


def baseline_of(results: list[Result]) -> dict[str, float]:
    """Each counted search's median time, keyed by case/target: what --baseline compares with."""
    return {result.key: round(result.median_ms, 2) for result in results if result.counted}


def from_screens(bot: Path, into: Path) -> int:
    """Cases from the screens darbit Studio saved for a bot (`.darbit/screens/`): one per screen. Says how many."""
    manifest = tomllib.loads((bot / "darbit.toml").read_text(encoding="utf-8"))
    images = bot / manifest.get("images", {}).get("folders", ["images"])[0]
    made = 0
    for places_file in sorted((bot / ".darbit" / "screens").glob("*.json")):
        places = json.loads(places_file.read_text(encoding="utf-8"))
        shot = places_file.with_suffix(".jpg")
        assets = places.get("assets", {})
        kept = [
            name
            for name, place in assets.items()
            if place.get("kind") == "image" and (images / f"{name}.png").is_file()
        ]
        if not shot.is_file() or not kept:
            continue
        case = into / places_file.stem
        (case / "images").mkdir(parents=True, exist_ok=True)
        shutil.copy(shot, case / "screen.jpg")
        lines = [f"# {bot.name}'s {places_file.stem} screen, saved by darbit Studio (JPEG)", 'screen = "screen.jpg"']
        lines += ['images = "images"', f"scale = {_scale_of(images, kept)}", ""]
        for name in kept:
            for source in _files_of(images, name):
                shutil.copy(source, case / "images" / source.name)
            lines += ["[[find]]", f'target = "{name}"', f"at = {assets[name]['box']}", ""]
        (case / "case.toml").write_text("\n".join(lines), encoding="utf-8", newline="\n")
        made += 1
    return made


def _files_of(images: Path, name: str) -> list[Path]:
    """An image's .png and .json, and the .json of the shared region it's searched in, if it names one."""
    files = [path for path in (images / f"{name}.png", images / f"{name}.json") if path.is_file()]
    if len(files) == 2:
        region = json.loads(files[1].read_text(encoding="utf-8")).get("region")
        if isinstance(region, str) and (images / f"{region}.json").is_file():
            files.append(images / f"{region}.json")
    return files


def _scale_of(images: Path, names: list[str]) -> float:
    """The display scaling the bot's images were taken at (their .json's `scale`), 1.0 if none says."""
    for name in names:
        settings = images / f"{name}.json"
        if settings.is_file():
            value = json.loads(settings.read_text(encoding="utf-8")).get("scale")
            if value:
                return float(value)
    return 1.0


def _print_table(results: list[Result]) -> None:
    print(f"{'case':16} {'target':24} {'answer':14} {'score':>6} {'median':>8} {'worst':>8} {'goal':>6}")
    for result in results:
        score = "" if result.score is None else f"{result.score:.3f}"
        timing = f"{result.median_ms:7.1f}ms {result.worst_ms:7.1f}ms" if result.counted else ""
        print(f"{result.case:16} {result.target:24} {result.answer:14} {score:>6} {timing:18} {result.goal_ms:4.0f}ms")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="darbit bench", description="Accuracy and speed of darbit's search on saved screens."
    )
    parser.add_argument("folders", nargs="*", type=Path, help="folders of cases (every case.toml under them)")
    parser.add_argument("--options", default="", help="matching options to turn on, comma separated")
    parser.add_argument("--repeat", type=int, default=15, help="searches per target, for the timing")
    parser.add_argument("--json", type=Path, help="also write the results here")
    parser.add_argument("--baseline", type=Path, help="fail when a search is much slower than in this file")
    parser.add_argument("--slower", type=float, default=SLOWER, help="how many times slower counts (default 2)")
    parser.add_argument("--save-baseline", type=Path, help="write this run's times as a baseline")
    parser.add_argument("--from-screens", nargs=2, type=Path, metavar=("BOT", "INTO"), help="make cases instead")
    args = parser.parse_args(argv)

    if args.from_screens:
        bot, into = args.from_screens
        made = from_screens(bot, into)
        print(f"{made} case(s) in {into}")
        return 0 if made else 1
    cases = cases_in(args.folders)
    if not cases:
        print("no case.toml found under " + ", ".join(str(folder) for folder in args.folders or [Path(".")]))
        return 1
    options = {part.strip() for part in args.options.split(",") if part.strip()}
    results: list[Result] = []
    for case in cases:
        results.extend(run_case(case, options, args.repeat))

    _print_table(results)
    counted = [result for result in results if result.counted]
    wrong = [result for result in counted if result.answer != "right"]
    over_goal = [result for result in counted if result.median_ms > result.goal_ms]
    print()
    print(f"{len(counted) - len(wrong)} of {len(counted)} right; {len(over_goal)} over their speed goal")
    slow = []
    if args.baseline:
        slow = slower_than(results, json.loads(args.baseline.read_text(encoding="utf-8")), args.slower)
        print(f"{len(slow)} more than {args.slower:g} times slower than {args.baseline}")
        for sentence in slow:
            print(f"  {sentence}")
    if args.json:
        args.json.write_text(json.dumps([asdict(result) for result in results], indent=2), encoding="utf-8")
    if args.save_baseline:
        args.save_baseline.write_text(json.dumps(baseline_of(results), indent=2) + "\n", encoding="utf-8")
    return 1 if wrong or slow else 0
