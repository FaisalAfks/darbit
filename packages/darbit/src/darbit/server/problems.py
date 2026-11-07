"""Why a bot's step failed, from what its run report already holds (round 13): the searches that ran out during the
step (each image, the closest it came against what it needs, for how long, the screenshots), the last things it did
before it, and the screen when it failed. Each failure gets a likely cause, said as a guess, and failures with the
same cause, step and reason are one problem on the Results page.
"""

import json
from dataclasses import dataclass, field
from pathlib import Path

from ..project.manifest import Project

COVERED = "covered"  # an image the bot found earlier today, suddenly far off: something over it, or another screen
CHANGED = "changed"  # close but under the line: the image looks a little different now
MISSING = "missing"  # far off and not seen today: not on screen, or the image is out of date
OWN = "own"  # nothing ran out: the bot's own reason
NEAR = 0.2  # how far under its line a closest match still counts as "a little different"
LONG = 30  # seconds of looking that make a missing image trouble; a shorter look is the bot checking, and its answer
DEFAULT_SIMILARITY = 0.7  # darbit's own, for a bot that names none
FAILING_AFTER = 2  # failures in a row that come down to the same image: it may have stopped matching
BEFORE = 8  # the steps before a failure shown with it
CLICKS = ("click", "double_click", "right_click", "drag")
LOOKS = ("exists", "wait", "find")

CAUSES = {
    COVERED: {"label": "Something covered the game", "tone": "warn", "act": False},
    CHANGED: {"label": "An image looks different now", "tone": "danger", "act": True},
    MISSING: {"label": "An image wasn't on screen", "tone": "danger", "act": True},
    OWN: {"label": "The bot's own reason", "tone": "info", "act": False},
}


@dataclass
class Search:
    """One image looked for and not found during a step, its searches added up."""

    target: str
    last: int = 0  # where in the run it last ran out: the last one before the failure decides
    seconds: float = 0.0
    closest: float = 0.0
    at: list | None = None
    screenshots: list[str] = field(default_factory=list)


def _name(target: object) -> str:
    text = str(target or "")
    return text.removesuffix(".png")


def _runs(events: list[dict]) -> list[tuple[dict, list[dict]]]:
    """Each failed step with the events of its run (from its start to its failure)."""
    found = []
    started: dict[str, int] = {}
    for index, event in enumerate(events):
        if event.get("event") != "step":
            continue
        path = str(event.get("step", ""))
        if event.get("state") == "started":
            started[path] = index
        elif event.get("state") == "failed":
            begin = started.pop(path, max(0, index - 200))
            found.append((event, events[begin:index]))
        elif path in started:
            started.pop(path)
    return found


def _searches(run: list[dict], watched: set[str]) -> list[Search]:
    """The images that ran out during a run, the last one before the failure first. A look with no wait (is it
    there right now?) and an image an observer watches for (it's meant not to be there) are left out."""
    by_name: dict[str, Search] = {}
    for index, event in enumerate(run):
        if "targets" not in event or event.get("found") is not None or event.get("closest") is None:
            continue
        if not event.get("timeout"):
            continue
        name = _name(event.get("closest_name") or event["targets"])
        if name in watched:
            continue
        search = by_name.setdefault(name, Search(name))
        search.last = index
        search.seconds += float(event.get("timeout") or 0)
        if float(event["closest"]) >= search.closest:
            search.closest = float(event["closest"])
            search.at = event.get("at")
        if event.get("screenshot"):
            search.screenshots.append(event["screenshot"])
    return sorted(by_name.values(), key=lambda search: -search.last)


def before(run: list[dict]) -> list[dict]:
    """The last things the bot did before a failure, oldest first: its clicks, its looks, the steps inside it and its
    moves between screens, each with whether it worked and a plain line."""
    found = []
    for event in run[1:]:  # the first is the failing step's own start
        row = _done(event)
        if row is not None:
            found.append(row)
    return found[-BEFORE:]


def _done(event: dict) -> dict | None:
    kind = str(event.get("event", ""))
    time = event.get("time")
    if kind in CLICKS:
        what = _name(event.get("target"))
        ok = bool(event.get("done"))
        say = f"{kind.replace('_', ' ')} {what}" if ok else f"{kind.replace('_', ' ')} {what}: not found"
        return {"time": time, "kind": kind, "what": what, "ok": ok, "say": say}
    if kind in LOOKS and "targets" in event:
        if event.get("found"):
            what = _name(event["found"])
            return {"time": time, "kind": kind, "what": what, "ok": True, "say": f"{kind} {what}: found"}
        what = _name(event.get("closest_name") or event["targets"])
        say = f"{kind} {what}: not there"
        if event.get("timeout"):
            say = f"{kind} {what}: not found in {_duration(float(event['timeout']))}"
        if event.get("closest") is not None:
            say += f" (closest {float(event['closest']):.2f})"
        return {"time": time, "kind": kind, "what": what, "ok": False, "say": say}
    if kind == "step":
        what = str(event.get("step", "")).split(" > ")[-1]
        state = str(event.get("state", ""))
        return {"time": time, "kind": kind, "what": what, "ok": state != "failed", "say": f"{what}: {state}"}
    if kind == "go":
        what = str(event.get("to", ""))
        state = str(event.get("state", ""))
        return {"time": time, "kind": kind, "what": what, "ok": state == "there", "say": f"go to {what}: {state}"}
    return None


def _watched(events: list[dict]) -> set[str]:
    """Images observers watch for."""
    found = set()
    for event in events:
        if event.get("event") == "observer" and event.get("name"):
            found.add(_name(event["name"]))
    return found


def _seen_today(events: list[dict]) -> set[str]:
    """Images found at least once today."""
    seen = set()
    for event in events:
        if "targets" in event and event.get("found"):
            seen.add(_name(event["found"]))
    return seen


def needs(project: Project, target: str) -> float:
    """The score an image needs: its own similarity, else the bot's, else darbit's."""
    for folder in _folders(project):
        settings_file = folder / (target + ".json")
        if settings_file.is_file():
            try:
                data = json.loads(settings_file.read_text(encoding="utf-8"))
            except (OSError, ValueError):
                data = {}
            if isinstance(data, dict) and data.get("similarity"):
                return float(data["similarity"])
    return float(project.settings.get("similarity", DEFAULT_SIMILARITY))


def _folders(project: Project) -> list[Path]:
    return [project.folder / name for name in project.images or ["images"]]


def cause_of(worst: Search | None, line: float, seen: set[str]) -> str:
    """The likely cause of a failure, from the image looked for longest before it."""
    if worst is None or worst.seconds < LONG:
        return OWN
    if worst.closest >= line - NEAR:
        return CHANGED
    if worst.target in seen:
        return COVERED
    return MISSING


def sentence(cause: str, worst: Search | None, line: float) -> str:
    """The failure in plain words: what the bot saw, and whether anything needs doing."""
    if worst is None:
        return "Nothing it looked for went missing first: this is the bot's own reason. It goes on by itself."
    if cause == OWN:
        return (
            f"It stopped when {worst.target} wasn't there after {_duration(worst.seconds)} (closest {worst.closest:.2f}): "
            "the bot's own check, so likely nothing to do. If it should have been there, retake it."
        )
    looked = f"It couldn't find {worst.target} for {_duration(worst.seconds)} (closest {worst.closest:.2f} of the {line:.2f} it needs)"
    if cause == COVERED:
        return (
            looked + ", though it found it earlier today. If another window was over the game, or the game was on "
            "another screen, nothing needs changing; if the game changed, retake it."
        )
    if cause == CHANGED:
        return looked + ": it's there but looks a little different now. Retake it, or lower what it needs."
    return looked + " and hasn't seen it today. The game may have been somewhere else, or the image is out of date."


def _duration(seconds: float) -> str:
    if seconds >= 90:
        return f"{round(seconds / 60)} minutes"
    return f"{round(seconds)} s"


def explain(project: Project, events: list[dict], logs: Path) -> list[dict]:
    """The day's failures grouped by likely cause, step, reason and image, the most frequent first."""
    seen = _seen_today(events)
    watched = _watched(events)
    screenshots = logs / "screenshots"
    groups: dict[tuple, dict] = {}
    for failure, run in _runs(events):
        searches = _searches(run, watched)
        worst = searches[0] if searches else None
        line = needs(project, worst.target) if worst else 0.0
        cause = cause_of(worst, line, seen)
        step = str(failure.get("step", ""))
        reason = str(failure.get("reason") or "failed")
        key = (cause, step.split(" > ")[-1], reason, worst.target if worst else "")
        group = groups.get(key)
        if group is None:
            group = {
                "cause": cause,
                **CAUSES[cause],
                "step": key[1],
                "path": step,
                "reason": reason,
                "sentence": sentence(cause, worst, line),
                "target": worst.target if worst else "",
                "count": 0,
                "times": [],
                "screenshot": None,
                "screenshots": [],
                "searches": [],
                "before": [],
            }
            groups[key] = group
        group["count"] += 1
        group["sentence"] = sentence(cause, worst, line)  # the latest failure's, like its searches
        group["times"].append(failure.get("time"))
        if failure.get("screenshot"):
            group["screenshot"] = _url(screenshots, failure["screenshot"])
        group["searches"] = [_search_row(project, search, screenshots) for search in searches[:4]]
        group["before"] = before(run)  # the latest failure's, like its searches
        for search in searches[:4]:
            for shot in search.screenshots:
                group["screenshots"].append(_url(screenshots, shot))
        if failure.get("screenshot"):
            group["screenshots"].append(_url(screenshots, failure["screenshot"]))
    found = list(groups.values())
    found.sort(key=lambda group: -group["count"])
    return found


def _search_row(project: Project, search: Search, screenshots: Path) -> dict:
    picture = None
    for folder in _folders(project):
        if (folder / (search.target + ".png")).is_file():
            picture = (folder / (search.target + ".png")).as_uri()
            break
    return {
        "target": search.target,
        "seconds": round(search.seconds),
        "closest": round(search.closest, 3),
        "needs": needs(project, search.target),
        "at": search.at,
        "picture": picture,
        "screenshot": _url(screenshots, search.screenshots[-1]) if search.screenshots else None,
    }


def _url(folder: Path, name: str) -> str | None:
    path = folder / name
    return path.as_uri() if path.is_file() else None


def failing(project: Project, events: list[dict]) -> dict | None:
    """An image that may have stopped matching: the last FAILING_AFTER or more failures all came down to it (it ran
    out before each), and it hasn't been found since the first of them. None when nothing is failing that way."""
    watched = _watched(events)
    streak: dict | None = None
    for failure, run in _runs(events):
        searches = _searches(run, watched)
        worst = searches[0] if searches else None
        if worst is None or worst.seconds < LONG:
            streak = None  # the bot's own reason, not an image
            continue
        if streak is not None and streak["target"] == worst.target:
            streak["count"] += 1
            streak["closest"] = max(streak["closest"], worst.closest)
            streak["step"] = str(failure.get("step", "")).split(" > ")[-1]
            streak["last"] = failure.get("time")
        else:
            streak = {
                "target": worst.target,
                "count": 1,
                "since": failure.get("time"),
                "last": failure.get("time"),
                "closest": worst.closest,
                "step": str(failure.get("step", "")).split(" > ")[-1],
            }
    if streak is None or streak["count"] < FAILING_AFTER:
        return None
    for event in events:
        if (
            event.get("found")
            and _name(event["found"]) == streak["target"]
            and str(event.get("time", "")) > str(streak["last"])
        ):
            return None  # found again after the last failure: it matches after all
    streak["needs"] = needs(project, streak["target"])
    streak["closest"] = round(streak["closest"], 3)
    streak["seen_before"] = _found_before(events, streak["target"], str(streak["since"]))
    streak["sentence"] = failing_sentence(streak)
    return streak


def _found_before(events: list[dict], target: str, moment: str) -> bool:
    for event in events:
        if str(event.get("time", "")) >= moment:
            return False
        if event.get("found") and _name(event["found"]) == target:
            return True
    return False


def failing_sentence(streak: dict) -> str:
    """What a failing image means, in plain words."""
    said = (
        f"{streak['step']} failed {streak['count']} times in a row waiting for it "
        f"(closest {streak['closest']:.2f} of the {streak['needs']:.2f} it needs)."
    )
    if streak.get("seen_before"):
        return (
            said
            + " It was found earlier today: a window over the game, or the game on another screen, does this too. If not, the game changed: retake it."
        )
    return said + " The game may have changed how it looks: retake it, and Highlight on screen shows what's found now."
