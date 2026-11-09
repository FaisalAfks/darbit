"""The Overview as blocks (round 14, C): the bot's author lays out its default in overview.toml and can add blocks of
their own (`d.show`, `@d.block`); the person using it arranges them in darbit Studio, which keeps their layout.

A block is {"kind", "shows", "title", "width"}: `kind` is how it's drawn, `shows` what it shows ("now", "round",
"next", "failures", "watching", "activity", "screen", "sees", "recoveries", "progress:<label>", "gain:<name>",
"block:<name>", "action:<name>") and `width` its share of a row of 12. `catalog` is every block a bot can have today,
`data` what each `shows` holds now, `default_layout` the author's layout (or one made from the old `[studio] tiles`).
"""

import tomllib
from datetime import datetime, timedelta
from pathlib import Path

from ..project.manifest import Project
from ..runtime import sees
from . import dashboard, history, problems, results

OVERVIEW = "overview.toml"
KINDS = ("now", "round", "list", "number", "ring", "chart", "text", "screen", "sees", "button", "recoveries")
WIDTHS = (3, 4, 6, 8, 12)
WEEK = 7


class OverviewError(ValueError):
    """An overview.toml that can't be used; the message says which block."""


def _block(kind: str, shows: str, title: str, width: int, origin: str = "darbit") -> dict:
    return {"kind": kind, "shows": shows, "title": title, "width": width, "origin": origin}


def catalog(project: Project, events: list[dict], actions: list[str]) -> list[dict]:
    """Every block this bot can show: darbit's own from what the bot records, then the bot's own and its actions."""
    found = [
        _block("now", "now", "Now", 8),
        _block("round", "round", "Today's round", 6),
        _block("list", "next", "Next up", 6),
        _block("list", "failures", "Problems", 6),
        _block("list", "watching", "Watching", 6),
        _block("list", "activity", "What happened", 6),
        _block("screen", "screen", "Last screen", 4),
        _block("recoveries", "recoveries", "Recoveries", 4),
        _block("sees", "sees", "What the bot sees", 8),  # off until added: it costs the bot a picture a second
    ]
    for label in _named(events, "progress", "label"):
        found.append(_block("ring", f"progress:{label}", label, 4))
    for name in _named(events, "gain", "name"):
        found.append(_block("number", f"gain:{name}", f"{name} today", 4))
        found.append(_block("chart", f"gain:{name}", f"{name} this week", 6))
    for name, kind in _shown(events).items():
        found.append(_block(kind, f"block:{name}", name, 4, project.name))
    for name in actions:
        found.append(_block("button", f"action:{name}", name, 4, project.name))
    return found


def _named(events: list[dict], event_kind: str, key: str) -> list[str]:
    names: list[str] = []
    for event in events:
        if event.get("event") == event_kind and event.get(key) and event[key] not in names:
            names.append(str(event[key]))
    return names


def _shown(events: list[dict]) -> dict[str, str]:
    """The bot's own blocks (`d.show`) with how each is best drawn: its kind, else a ring with a total, a list for a
    list, a number for a number, else text."""
    kinds: dict[str, str] = {}
    for event in events:
        if event.get("event") != "block" or not event.get("name"):
            continue
        value = event.get("value")
        kind = event.get("kind")
        if not kind:
            if event.get("total") is not None:
                kind = "ring"
            elif isinstance(value, list):
                kind = "list"
            elif isinstance(value, (int, float)) and not isinstance(value, bool):
                kind = "number"
            else:
                kind = "text"
        kinds[str(event["name"])] = kind
    return kinds


def default_layout(project: Project, blocks: list[dict]) -> list[dict]:
    """The author's layout from overview.toml; without one, darbit's (the old `[studio] tiles`, or all of its own)."""
    path = project.folder / OVERVIEW
    if path.is_file():
        return read_layout(path)
    return default_layout_without_file(project, blocks)


def default_layout_without_file(project: Project, blocks: list[dict]) -> list[dict]:
    """darbit's layout: the old `[studio] tiles` in order, or all of darbit's own blocks with the recoveries last."""
    wanted = project.tiles or dashboard.DEFAULT_TILES
    layout: list[dict] = []
    for name in wanted:
        kind, _, label = name.partition(":")
        for block in blocks:
            if _old_tile_wants(kind, label, block) and block not in layout:
                layout.append(block)
    if not project.tiles:
        for block in blocks:
            if block["kind"] == "recoveries":
                layout.append(block)
    return layout


def _old_tile_wants(kind: str, label: str, block: dict) -> bool:
    shows = block["shows"]
    if kind in ("now", "round"):
        return shows == kind
    if kind in ("next", "watching", "activity", "failures"):
        return shows == kind
    if kind == "progress":
        return shows == f"progress:{label}" if label else shows.startswith("progress:")
    if kind == "gains":
        return shows.startswith("gain:") and block["kind"] == "number"
    return False


def read_layout(path: Path) -> list[dict]:
    """overview.toml's [[block]] entries, checked."""
    try:
        data = tomllib.loads(path.read_text(encoding="utf-8"))
    except (OSError, tomllib.TOMLDecodeError) as error:
        raise OverviewError(f"{path.name}: {error}") from None
    layout = []
    for index, entry in enumerate(data.get("block", []), start=1):
        if not isinstance(entry, dict):
            raise OverviewError(f"{path.name}: block {index} is a table")
        kind = entry.get("kind")
        if kind not in KINDS:
            raise OverviewError(f"{path.name}: block {index}'s kind is one of {', '.join(KINDS)}, not {kind!r}")
        shows = str(entry.get("shows") or kind)
        width = entry.get("width", 4)
        if width not in WIDTHS:
            raise OverviewError(f"{path.name}: block {index}'s width is one of {WIDTHS}, not {width!r}")
        layout.append(_block(kind, shows, str(entry.get("title") or shows), width, "bot"))
    return layout


def data(project: Project, events: list[dict], day: str, now: datetime, logs: Path, actions: list[str] = ()) -> dict:
    """What each block's `shows` holds now."""
    found: dict[str, object] = {}
    found["now"] = dashboard.now_tile(events).data
    found["round"] = _tile_data(dashboard.round_tile(events))
    found["next"] = _tile_data(dashboard.next_tile(events, now))
    found["failures"] = _tile_data(dashboard.failures_tile(events))
    found["watching"] = _tile_data(dashboard.watching_tile(events))
    found["activity"] = _tile_data(dashboard.activity_tile(events))
    found["screen"] = {"picture": _last_screen(logs)}
    found["sees"] = {"look": str(logs / sees.LOOK), "logs": str(logs)}  # the Studio follows the file while shown
    found["setup"] = _tile_data(dashboard.setup_tile(project))
    found["problems"] = problems.explain(project, events, logs)
    found["failing"] = problems.failing(project, events)  # an image that may have stopped matching
    found["recoveries"] = recoveries(events, day)
    progress = _tile_data(dashboard.progress_tile(events)) or {"items": []}
    for item in progress.get("items", []):
        found[f"progress:{item['label']}"] = item
    gains = _tile_data(dashboard.gains_tile(events)) or {"items": []}
    week = _week_of_gains(project, day)
    for item in gains.get("items", []):
        found[f"gain:{item['name']}"] = {**item, "week": week.get(item["name"], [0] * WEEK)}
    for name in actions:
        found[f"action:{name}"] = {"name": name}
    for event in events:
        if event.get("event") == "block" and event.get("name"):
            found[f"block:{event['name']}"] = {key: value for key, value in event.items() if key not in ("event",)}
    return found


def recoveries(events: list[dict], day: str) -> dict:
    """How often the bot got itself going again today (d.record.recovered): the count, the most common reason, the
    last one (`at` in seconds since the day began) and each `how` with its count and its whys."""
    hows = results.recoveries_of(events)
    reasons: dict[str, int] = {}
    count = 0
    for row in hows:
        count += row["count"]
        for why, times in row["whys"].items():
            reasons[why] = reasons.get(why, 0) + times
    reason = ""
    reason_count = 0
    for why, times in reasons.items():
        if times > reason_count:
            reason = why
            reason_count = times
    last = None
    for event in events:
        if event.get("event") == "recovered":
            last = event
    last_one = None
    if last is not None:
        last_one = {
            "at": results.seconds_of(last.get("time"), day),
            "how": str(last.get("how", "recovered")),
            "why": str(last.get("why", "")) or "no reason given",
        }
    return {"count": count, "reason": reason, "reason_count": reason_count, "last": last_one, "hows": hows}


def _tile_data(tile: object) -> dict | None:
    return tile.data if tile is not None else None


def _last_screen(logs: Path) -> str | None:
    folder = logs / "screenshots"
    if not folder.is_dir():
        return None
    newest = None
    for path in folder.glob("*.jpg"):
        if newest is None or path.stat().st_mtime > newest.stat().st_mtime:
            newest = path
    return newest.as_uri() if newest is not None else None


def _week_of_gains(project: Project, day: str) -> dict[str, list[float]]:
    """Each gain's amount on each of the week's days, the day itself last."""
    last = datetime.fromisoformat(day)
    days = [(last - timedelta(days=back)).strftime("%Y-%m-%d") for back in range(WEEK - 1, -1, -1)]
    found: dict[str, list[float]] = {}
    for index, name in enumerate(days):
        try:
            events = history.events(project, name, kinds=("gain",))  # a week of every event is tens of MB of JSON
        except (OSError, ValueError):
            continue
        for event in events:
            if not isinstance(event.get("amount"), (int, float)):
                continue
            row = found.setdefault(str(event.get("name")), [0] * WEEK)
            row[index] += event["amount"]
    return found
