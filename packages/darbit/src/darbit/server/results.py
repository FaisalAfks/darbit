"""The Results page in darbit Studio: what a bot got each day and what went wrong (decision 0013, round 5).

`days(project)` lists the days with a run report, newest first, each with its lead gain and run time.
`day(project, "2026-10-26")` is one day in full: when it ran, its gains (today, each of the last 7 days, the
last total), progress, how many top-level steps finished, the time lost to failures, the problems grouped by
cause, and the timeline lanes. All of it comes from the run report (`d.record.gain`, `d.progress` and steps), through the run history in SQLite
(history.py).
"""

from datetime import date, timedelta

from ..project.manifest import Project
from . import history

WEEK = 7  # days in the gains' small bar charts
DAYS_LISTED = 60  # days in the day list


def seconds_of(time: object, day: str = "") -> float | None:
    """A report time ("2026-10-26T10:04:31.120" or "10:04:31") as seconds since midnight; with `day`, since the
    midnight that day began, so a bot's day that starts at 03:00 runs on past 24 h (clockOf still reads "01:00")."""
    if not isinstance(time, str) or not time:
        return None
    later = 0
    if day and "T" in time:
        try:
            later = (date.fromisoformat(time.split("T")[0]) - date.fromisoformat(day)).days
        except ValueError:
            later = 0
    clock = time.split("T")[-1]
    parts = clock.split(":")
    if len(parts) < 2:
        return None
    try:
        hours = int(parts[0])
        minutes = int(parts[1])
        seconds = 0.0
        if len(parts) > 2:
            seconds = float(parts[2])
    except ValueError:
        return None
    return later * 86400 + hours * 3600 + minutes * 60 + seconds


def gains_of(events: list[dict]) -> dict[str, dict]:
    """Each gain's name -> {"amount": summed, "total": last total, "icon": last icon}, in first-seen order."""
    found: dict[str, dict] = {}
    for event in events:
        if event.get("event") != "gain" or not event.get("name"):
            continue
        amount = event.get("amount")
        if not isinstance(amount, (int, float)):
            continue
        row = found.setdefault(event["name"], {"amount": 0, "total": None, "icon": None})
        row["amount"] += amount
        if event.get("total") is not None:
            row["total"] = event["total"]
        if event.get("icon"):
            row["icon"] = event["icon"]
    return found


def report_days(project: Project) -> list[str]:
    """The days with a run report, newest first."""
    history.catch_up(project)
    return history.days(project)


def _top_steps(events: list[dict], day: str = "") -> list[dict]:
    """Each top-level step run: {"name", "start", "end", "state", "seconds", "reason", "screenshot"}."""
    runs: list[dict] = []
    open_runs: dict[str, dict] = {}
    for event in events:
        if event.get("event") != "step" or not event.get("step"):
            continue
        name = event["step"]
        if " > " in name:
            continue
        at = seconds_of(event.get("time"), day)
        if event.get("state") == "started":
            run = {
                "name": name,
                "start": at,
                "end": None,
                "state": "running",
                "seconds": None,
                "reason": None,
                "screenshot": None,
            }
            open_runs[name] = run
            runs.append(run)
            continue
        run = open_runs.pop(name, None)
        if run is None:
            continue
        run["end"] = at
        run["state"] = event.get("state")
        run["seconds"] = event.get("seconds")
        run["reason"] = event.get("reason")
        run["screenshot"] = event.get("screenshot")
    return runs


def _problems(events: list[dict]) -> list[dict]:
    """Failed steps grouped by what failed and why, most frequent first."""
    groups: dict[tuple[str, str], dict] = {}
    for event in events:
        if event.get("event") != "step" or event.get("state") != "failed":
            continue
        step = str(event.get("step", ""))
        reason = str(event.get("reason") or "failed")
        key = (step.split(" > ")[-1], reason)
        group = groups.setdefault(
            key, {"step": key[0], "path": step, "reason": reason, "count": 0, "times": [], "screenshot": None}
        )
        group["count"] += 1
        group["times"].append(event.get("time"))
        if event.get("screenshot"):
            group["screenshot"] = event["screenshot"]
    found = list(groups.values())
    found.sort(key=_by_count, reverse=True)
    return found


def _by_count(group: dict) -> int:
    return group["count"]


def _progress(events: list[dict]) -> list[dict]:
    latest: dict[str, dict] = {}
    for event in events:
        if event.get("event") == "progress" and event.get("label"):
            latest[event["label"]] = {"label": event["label"], "done": event.get("done"), "total": event.get("total")}
    return list(latest.values())


def _week_before(day: str) -> list[str]:
    """The 7 days ending with `day`, oldest first."""
    last = date.fromisoformat(day)
    found = []
    for back in range(WEEK - 1, -1, -1):
        found.append((last - timedelta(days=back)).isoformat())
    return found


def day(project: Project, day_name: str) -> dict:
    """One day of the Results page."""
    history.catch_up(project)
    events = history.events(project, day_name)
    times = []
    for event in events:
        at = seconds_of(event.get("time"), day_name)
        if at is not None:
            times.append(at)
    today = gains_of(events)
    week_days = _week_before(day_name)
    week: dict[str, list[float]] = {}
    for name in today:
        week[name] = []
    for other in week_days:
        other_gains = today
        if other != day_name:
            other_gains = gains_of(history.events(project, other, kinds=("gain",)))
        for name, amounts in week.items():
            amount = 0
            if name in other_gains:
                amount = other_gains[name]["amount"]
            amounts.append(amount)
    gains = []
    for name, row in today.items():
        gains.append(
            {"name": name, "today": row["amount"], "total": row["total"], "icon": row["icon"], "week": week[name]}
        )
    steps = _top_steps(events, day_name)
    ended = 0
    finished = 0
    lost = 0.0
    lanes: dict[str, list[dict]] = {}
    for run in steps:
        lanes.setdefault(run["name"], []).append({"start": run["start"], "end": run["end"], "state": run["state"]})
        if run["state"] == "running":
            continue
        ended += 1
        if run["state"] == "ok":
            finished += 1
        if run["state"] == "failed" and isinstance(run["seconds"], (int, float)):
            lost += run["seconds"]
    lane_list = []
    for name, blocks in lanes.items():
        lane_list.append({"name": name, "blocks": blocks})
    start = None
    end = None
    if times:
        start = min(times)
        end = max(times)
    return {
        "day": day_name,
        "start": start,
        "end": end,
        "week_days": week_days,
        "gains": gains,
        "progress": _progress(events),
        "finished": {"done": finished, "total": ended},
        "lost_seconds": round(lost),
        "problems": _problems(events),
        "recoveries": recoveries_of(events),
        "lanes": lane_list,
    }


def recoveries_of(events: list[dict]) -> list[dict]:
    """How the bot recovered (d.record.recovered), most often first: each `how` with its count and its whys."""
    found: dict[str, dict] = {}
    for event in events:
        if event.get("event") != "recovered":
            continue
        how = str(event.get("how", "recovered"))
        why = str(event.get("why", "")) or "no reason given"
        row = found.setdefault(how, {"how": how, "count": 0, "whys": {}})
        row["count"] += 1
        row["whys"][why] = row["whys"].get(why, 0) + 1
    rows = sorted(found.values(), key=_count, reverse=True)
    for row in rows:
        row["whys"] = dict(sorted(row["whys"].items(), key=_second, reverse=True))
    return rows


def _count(row: dict) -> int:
    return row["count"]


def _second(pair: tuple) -> int:
    return pair[1]


def days(project: Project) -> list[dict]:
    """The day list: each day with a report, its lead gain, how long it ran and how many problems it had."""
    found = []
    for name in report_days(project)[:DAYS_LISTED]:
        events = history.events(project, name, kinds=("gain", "step"))
        gains = gains_of(events)
        lead = None
        for gain_name, row in gains.items():
            lead = {"name": gain_name, "amount": row["amount"], "icon": row["icon"]}
            break
        failures = 0
        for event in events:
            if event.get("event") == "step" and event.get("state") == "failed":
                failures += 1
        seconds = 0
        span = history.span(project, name)
        if span is not None:
            first = seconds_of(span[0], name)
            last = seconds_of(span[1], name)
            if first is not None and last is not None:
                seconds = round(last - first)
        found.append({"day": name, "lead": lead, "seconds": seconds, "problems": failures})
    return found


def day_lines(day: dict) -> list[str]:
    """A day's results as lines of text."""
    lines = [f"{day['day']}"]
    if day.get("start") is not None and day.get("end") is not None:
        lines[0] += f", {clock(day['start'])} to {clock(day['end'])}"
    finished = day.get("finished") or {}
    lines.append(f"steps finished: {finished.get('done', 0)} of {finished.get('total', 0)}")
    for gain in day.get("gains", []):
        total = f" (total {gain['total']})" if gain.get("total") is not None else ""
        lines.append(f"gained {gain['today']} {gain['name']}{total}")
    for problem in day.get("problems", []):
        lines.append(f"problem x{problem['count']}: {problem['step']}: {problem['reason']}")
    for recovery in day.get("recoveries", []):
        whys = []
        for why, count in recovery["whys"].items():
            whys.append(f"{why} {count}")
        lines.append(f"{recovery['how']} x{recovery['count']}: {', '.join(whys)}")
    if day.get("lost_seconds"):
        lines.append(f"time lost to failures: {clock(day['lost_seconds'])}")
    return lines


def clock(seconds: float) -> str:
    whole = int(seconds)
    return f"{whole // 3600}:{whole % 3600 // 60:02d}:{whole % 60:02d}"
