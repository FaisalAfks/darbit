"""A bot's Overview in darbit Studio, built from its run report (decision 0011, T30).

`tiles(project)` reads `.darbit/logs/report-<day>.jsonl` and returns the tiles in order: now (the open steps),
round (each top-level step), progress, next, activity, failures, watching and setup. The bot needs no extra
code for most of them; `[studio] tiles` in darbit.toml picks and orders them. A tile with nothing to show is
left out, except "now".
"""

import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from .. import paths
from ..platform import system
from ..platform.backend import NotSupported
from ..project.manifest import Project

DEFAULT_TILES = ["now", "round", "progress", "gains", "next", "activity", "failures", "watching", "setup"]
ACTIVITY_SHOWN = 50  # newest events in the Activity tile
# events that are darbit's own detail, not something that happened worth showing
DETAIL = {
    "step",
    "progress",
    "next",
    "gain",
    "plan",
    "observer",
    "exists",
    "wait",
    "vanish",
    "find_all",
    "click",
    "double_click",
    "right_click",
    "hover",
    "drag",
    "scroll",
}


@dataclass
class Tile:
    kind: str  # one of DEFAULT_TILES
    title: str
    data: dict = field(default_factory=dict)  # plain values, ready to send as JSON


def report_file(project: Project, day: str) -> Path:
    """The project's run report for a day ("2026-10-26")."""
    logs = paths.project_dir(project.folder) / "logs"
    if "logs" in project.settings:
        logs = project.folder / project.settings["logs"]
    return logs / f"report-{day}.jsonl"


def read_events(path: Path) -> list[dict]:
    """Every event in a run report, oldest first; a broken line is skipped.

    A running bot only adds lines, so what's been read is kept and only the new lines are read next time (a day's
    report is a few MB; reading it all again every couple of seconds kept a core busy). The list is shared: don't
    change it or its events.
    """
    if not path.is_file():
        _read.pop(path, None)
        return []
    size = path.stat().st_size
    known = _read.get(path)
    if known is None or size < known.offset or not _only_grew(path, known):
        known = _Read()  # new, or written again from the start
    if size > known.offset:
        with path.open("rb") as file:
            file.seek(known.offset)
            data = file.read(size - known.offset)
        end = data.rfind(b"\n") + 1  # a line still being written waits for next time
        if end < len(data) and _whole(data[end:]):
            end = len(data)  # the last line has no line break but is whole
        if end:
            known.tail = (known.tail + data[:end])[-TAIL:]
        for line in data[:end].splitlines():
            try:
                event = json.loads(line)
            except ValueError:
                continue
            if isinstance(event, dict):
                known.events.append(event)
        known.offset += end
    _read.pop(path, None)
    _read[path] = known  # newest last
    while len(_read) > KEEP_READ:
        _read.pop(next(iter(_read)))
    return known.events


class _Read:
    def __init__(self) -> None:
        self.offset = 0  # bytes read so far
        self.tail = b""  # the last bytes read, to tell a report that grew from one written again
        self.events: list[dict] = []


def _whole(line: bytes) -> bool:
    try:
        json.loads(line)
    except ValueError:
        return False
    return True


def _only_grew(path: Path, known: _Read) -> bool:
    """The bytes read last time are still where they were: the report only grew."""
    if not known.tail:
        return True
    with path.open("rb") as file:
        file.seek(known.offset - len(known.tail))
        return file.read(len(known.tail)) == known.tail


_read: dict[Path, _Read] = {}
KEEP_READ = 3  # reports kept read: today's, and a couple the Results page looked at
TAIL = 256  # bytes compared to tell a report that grew from one written again


def tiles(project: Project, day: str | None = None, now: datetime | None = None) -> list[Tile]:
    """The Overview's tiles for one day of the project's run report (today by default)."""
    if now is None:
        now = datetime.now()
    if day is None:
        day = now.strftime("%Y-%m-%d")
    events = read_events(report_file(project, day))
    wanted = project.tiles or DEFAULT_TILES
    shown = []
    for name in wanted:
        kind, _, label = name.partition(":")
        tile = _build(kind, label, events, project, now)
        if tile is not None:
            shown.append(tile)
    return shown


def _build(kind: str, label: str, events: list[dict], project: Project, now: datetime) -> Tile | None:
    if kind == "now":
        return now_tile(events)
    if kind == "round":
        return round_tile(events)
    if kind == "progress":
        return progress_tile(events, label)
    if kind == "gains":
        return gains_tile(events)
    if kind == "next":
        return next_tile(events, now)
    if kind == "activity":
        return activity_tile(events)
    if kind == "failures":
        return failures_tile(events)
    if kind == "watching":
        return watching_tile(events)
    if kind == "setup":
        return setup_tile(project)
    return None


def _steps(events: list[dict]) -> list[dict]:
    found = []
    for event in events:
        if event.get("event") == "step" and event.get("step"):
            found.append(event)
    return found


def _ended_without_saying(started: dict) -> bool:
    """Whether a step's bot has gone (killed, crashed, closed) while the step was open: its process isn't running.
    Steps from before steps carried their process stay as they were."""
    pid = started.get("pid")
    if not isinstance(pid, int):
        return False
    try:
        return not system.process_alive(pid)
    except NotSupported:
        return False


def now_tile(events: list[dict]) -> Tile:
    """The steps still open, deepest last: ["Speed Raid", "Sakura", "Fight"], since when, and since when the bot
    has been waiting for a locked screen (None when it isn't)."""
    open_steps: dict[str, str] = {}  # step path -> started
    for event in _steps(events):
        if event.get("state") == "started" and not _ended_without_saying(event):
            open_steps[event["step"]] = event.get("time", "")
        else:
            open_steps.pop(event["step"], None)
    deepest = ""
    for step in open_steps:
        if step.count(" > ") >= deepest.count(" > "):
            deepest = step
    locked = _locked_since(events)
    if not deepest:
        return Tile("now", "Now", {"path": [], "since": None, "locked": locked})
    return Tile("now", "Now", {"path": deepest.split(" > "), "since": open_steps[deepest], "locked": locked})


def _locked_since(events: list[dict]) -> str | None:
    """When the screen was locked, if the bot is still waiting for it (its last `screen` event)."""
    last = None
    for event in events:
        if event.get("event") == "screen":
            last = event
    if last is not None and last.get("state") == "locked":
        return last.get("time")
    return None


def round_tile(events: list[dict]) -> Tile | None:
    """Each top-level step (a mode, for most bots): when it last started, how it ended and how long it took.

    Steps named in the last `d.plan` that haven't started yet come after, as "planned".
    """
    rows: dict[str, dict] = {}
    planned: list[str] = []
    for event in events:
        if event.get("event") == "plan" and isinstance(event.get("steps"), list):
            planned = [str(name) for name in event["steps"]]
    for event in _steps(events):
        name = event["step"]
        if " > " in name:
            continue
        if event.get("state") == "started":
            state = "stopped" if _ended_without_saying(event) else "running"
            rows[name] = {"name": name, "started": event.get("time"), "state": state, "seconds": None}
        elif name in rows:
            rows[name]["state"] = event.get("state")
            rows[name]["seconds"] = event.get("seconds")
            if event.get("reason"):
                rows[name]["reason"] = event["reason"]
    for name in planned:
        if name not in rows:
            rows[name] = {"name": name, "started": None, "state": "planned", "seconds": None}
    if not rows:
        return None
    ordered = list(rows.values())
    if planned:
        ordered = _in_plan_order(ordered, planned)
    return Tile("round", "Today's round", {"steps": ordered})


def _in_plan_order(rows: list[dict], planned: list[str]) -> list[dict]:
    """The planned steps in plan order, then any others in the order they ran."""
    by_name = {}
    for row in rows:
        by_name[row["name"]] = row
    ordered = []
    for name in planned:
        if name in by_name:
            ordered.append(by_name.pop(name))
    for row in rows:
        if row["name"] in by_name:
            ordered.append(row)
    return ordered


def progress_tile(events: list[dict], label: str = "") -> Tile | None:
    """The last value of each d.progress, or of one label."""
    latest: dict[str, dict] = {}
    for event in events:
        if event.get("event") != "progress":
            continue
        if label and event.get("label") != label:
            continue
        latest[event.get("label", "")] = {
            "label": event.get("label"),
            "done": event.get("done"),
            "total": event.get("total"),
        }
    if not latest:
        return None
    title = label or "Progress"
    return Tile("progress", title, {"items": list(latest.values())})


def gains_tile(events: list[dict]) -> Tile | None:
    """Today's gains from d.record.gain: each name with its sum today and its last total."""
    found: dict[str, dict] = {}
    for event in events:
        if event.get("event") != "gain" or not event.get("name"):
            continue
        amount = event.get("amount")
        if not isinstance(amount, (int, float)):
            continue
        row = found.setdefault(event["name"], {"name": event["name"], "today": 0, "total": None, "icon": None})
        row["today"] += amount
        if event.get("total") is not None:
            row["total"] = event["total"]
        if event.get("icon"):
            row["icon"] = event["icon"]
    if not found:
        return None
    return Tile("gains", "Gains today", {"items": list(found.values())})


def next_tile(events: list[dict], now: datetime) -> Tile | None:
    """The next time of each d.next that is still ahead, soonest first."""
    latest: dict[str, str] = {}
    for event in events:
        if event.get("event") == "next" and event.get("label") and event.get("at"):
            latest[event["label"]] = event["at"]
    ahead = []
    for label, at in latest.items():
        when = _parse_time(at)
        if when is None:
            continue
        if when.tzinfo is not None:
            current = datetime.now(when.tzinfo)
        else:
            current = now
        if when >= current:
            ahead.append({"label": label, "at": at, "in_seconds": round((when - current).total_seconds())})
    if not ahead:
        return None
    ahead.sort(key=_seconds_away)
    return Tile("next", "Next up", {"items": ahead})


def _seconds_away(item: dict) -> int:
    return item["in_seconds"]


def _parse_time(text: str) -> datetime | None:
    try:
        return datetime.fromisoformat(text)
    except (TypeError, ValueError):
        return None


def activity_tile(events: list[dict]) -> Tile | None:
    """The bot's own events (d.record), newest first."""
    rows = []
    for event in events:
        if event.get("event") in DETAIL:
            continue
        fields = {}
        for key, value in event.items():
            if key not in ("time", "event"):
                fields[key] = value
        rows.append({"time": event.get("time"), "event": event.get("event"), "fields": fields})
    if not rows:
        return None
    rows.reverse()
    return Tile("activity", "What happened", {"items": rows[:ACTIVITY_SHOWN]})


def failures_tile(events: list[dict]) -> Tile | None:
    """Steps that failed, newest first, with their reason and screenshot."""
    rows = []
    for event in _steps(events):
        if event.get("state") == "failed":
            rows.append(
                {
                    "time": event.get("time"),
                    "step": event.get("step"),
                    "reason": event.get("reason"),
                    "screenshot": event.get("screenshot"),
                }
            )
    if not rows:
        return None
    rows.reverse()
    return Tile("failures", "Failures", {"items": rows})


def watching_tile(events: list[dict]) -> Tile | None:
    """Each observer: whether it's watching, and how often it fired today."""
    rows: dict[str, dict] = {}
    for event in events:
        if event.get("event") != "observer" or not event.get("name"):
            continue
        name = event["name"]
        row = rows.setdefault(name, {"name": name, "state": "watching", "fired": 0, "last_fired": None})
        if event.get("state") == "fired":
            row["fired"] += 1
            row["last_fired"] = event.get("time")
        elif event.get("state") in ("watching", "stopped"):
            row["state"] = event["state"]
    if not rows:
        return None
    return Tile("watching", "Watching", {"items": list(rows.values())})


def setup_tile(project: Project) -> Tile | None:
    """How many of the setup guide's pictures are taken, when the bot has a guide.toml."""
    guide_file = project.folder / "guide.toml"
    if not guide_file.is_file():
        return None
    from ..capture.guide import GuideError, load, progress

    try:
        guide = load(guide_file)
    except GuideError as error:
        return Tile("setup", "Setup", {"error": str(error)})
    folder = project.folder / (project.images[0] if project.images else "images")
    done = progress(guide, folder)
    current = None
    if done.current is not None:
        current = {"name": done.current.name, "screen": done.current.screen.name, "say": done.current.take.say}
    return Tile("setup", "Setup", {"done": done.done, "total": done.total, "current": current})
