"""What a bot earns, by currency (decision 0023): the Wallet block (each balance now and today's change), the Gains by
source block (a currency's gains split by where they came from, today and the week) and each run's gains on Results.

A gain's currency is its name; its source is the `source` it was given, else the top-level step it was recorded in,
else "other". A gain from before gains carried their step counts under the step open when it was recorded.
"""

from dataclasses import dataclass, field

from . import results

OTHER = "other"
MOST_SOURCES = 6  # sources a currency is split into (one colour each); the rest count as "other"


@dataclass
class Gain:
    name: str
    amount: float
    source: str
    run: str  # the top-level step open when it was recorded, or ""
    detail: str  # what the run's line adds: the source when it isn't the run, or the step inside it


def gains_with_sources(events: list[dict]) -> list[Gain]:
    """Each gain in `events` with its source and run. With the day's steps in `events`, a gain that doesn't say
    its step gets the one open when it was recorded."""
    found = []
    open_run = ""
    for event in events:
        kind = event.get("event")
        if kind == "step":
            open_run = _next_open_run(event, open_run)
            continue
        if kind != "gain" or not event.get("name"):
            continue
        amount = event.get("amount")
        if not isinstance(amount, (int, float)) or isinstance(amount, bool):
            continue
        path = _path_of(event)
        run = path[0] if path else open_run
        source = str(event.get("source") or "") or run or OTHER
        detail = ""
        if source != run and run:
            detail = source
        elif len(path) > 1:
            detail = path[1]
        found.append(Gain(str(event["name"]), amount, source, run, detail))
    return found


def _next_open_run(event: dict, open_run: str) -> str:
    step = str(event.get("step") or "")
    if not step or " > " in step:
        return open_run
    if event.get("state") == "started":
        return step
    if step == open_run:
        return ""
    return open_run


def _path_of(event: dict) -> list[str]:
    step = event.get("step")
    if not isinstance(step, str) or not step:
        return []
    return step.split(" > ")


# ---- the Wallet


def wallet(earlier: list[dict], today: list[dict], day: str) -> dict:
    """Each currency's balance now (its last `d.record.balance`, or a gain's total if newer) with when it was read,
    and today's change: what it gained today, or for a currency with no gains today the change since its first read
    today. `earlier` is the days before's gains and balances, oldest first. {"items": [...], "read": {...} or None}."""
    rows: dict[str, dict] = {}
    for event in earlier + today:
        value = _balance_in(event)
        if value is None:
            continue
        row = rows.setdefault(str(event["name"]), {"name": str(event["name"]), "icon": None, "value": value})
        row["value"] = value
        row["at"] = results.seconds_of(event.get("time"), day)
        row["where"] = _path_of(event)[0] if _path_of(event) else ""
        if event.get("icon"):
            row["icon"] = event["icon"]
    for name, row in rows.items():
        row["today"] = _change_today(name, today)
    last = None
    for row in rows.values():
        if row.get("at") is not None and (last is None or row["at"] >= last["at"]):
            last = {"at": row["at"], "where": row["where"]}
    return {"items": list(rows.values()), "read": last}


def _balance_in(event: dict) -> float | None:
    """The balance an event says: a balance's value, or a gain's total."""
    if not event.get("name"):
        return None
    value = None
    if event.get("event") == "balance":
        value = event.get("value")
    elif event.get("event") == "gain":
        value = event.get("total")
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        return None
    return value


def _change_today(name: str, today: list[dict]) -> float:
    gained = 0
    any_gain = False
    first = None
    last = None
    for event in today:
        if event.get("name") != name:
            continue
        amount = event.get("amount")
        if event.get("event") == "gain" and isinstance(amount, (int, float)) and not isinstance(amount, bool):
            gained += amount
            any_gain = True
        if event.get("event") == "balance":
            value = _balance_in(event)
            if value is not None:
                first = value if first is None else first
                last = value
    if any_gain or first is None:
        return gained
    return last - first


def has_balances(events: list[dict]) -> bool:
    """Whether any event says a balance (the Wallet block has something to show)."""
    for event in events:
        if _balance_in(event) is not None:
            return True
    return False


# ---- Gains by source


def by_source(name: str, week: list[list[Gain]]) -> dict:
    """One currency's gains split by source: today's (the week's last day) and each day of the week, in one order of
    sources, most first, so every bar gives a source the same place and colour."""
    totals: dict[str, float] = {}
    for gains in week:
        for gain in gains:
            if gain.name == name:
                totals[gain.source] = totals.get(gain.source, 0) + gain.amount
    order = sorted(totals, key=totals.get, reverse=True)
    if len(order) > MOST_SOURCES:
        order = [source for source in order[: MOST_SOURCES - 1] if source != OTHER] + [OTHER]
    days = []
    for gains in week:
        amounts = [0] * len(order)
        for gain in gains:
            if gain.name != name:
                continue
            place = order.index(gain.source) if gain.source in order else order.index(OTHER)
            amounts[place] += gain.amount
        days.append(amounts)
    today = days[-1] if days else [0] * len(order)
    return {"name": name, "sources": order, "today": today, "week": days}


# ---- each run, on Results


@dataclass
class _Run:
    start: float | None
    name: str
    details: list[str] = field(default_factory=list)
    gains: dict[str, float] = field(default_factory=dict)


def runs(events: list[dict], day: str) -> dict:
    """Each run (a top-level step, or a gain outside every step) that gained something: when it started, its name
    with what it was for, and its gains by currency; then each source's runs and gains, most of the day's first
    currency first. {"currencies": [...], "runs": [...], "by_source": [...]}."""
    rows: list[_Run] = []
    currencies: list[str] = []
    current: _Run | None = None
    outside: _Run | None = None
    sources: dict[str, dict] = {}
    for event in events:
        kind = event.get("event")
        step = str(event.get("step") or "")
        if kind == "step" and step and " > " not in step:
            outside = None
            if event.get("state") == "started":
                current = _Run(results.seconds_of(event.get("time"), day), step)
                rows.append(current)
            elif current is not None and current.name == step:
                current = None
            continue
        if kind != "gain":
            continue
        gain = _one_gain(event, current)
        if gain is None:
            continue
        run = current
        if run is None or (gain.run and gain.run != run.name):
            name = gain.run or gain.source
            if outside is None or outside.name != name:  # gains one after another outside a run make one line
                outside = _Run(results.seconds_of(event.get("time"), day), name)
                rows.append(outside)
            run = outside
        if gain.name not in currencies:
            currencies.append(gain.name)
        run.gains[gain.name] = run.gains.get(gain.name, 0) + gain.amount
        if gain.detail and gain.detail not in run.details:
            run.details.append(gain.detail)
        row = sources.setdefault(gain.source, {"source": gain.source, "runs": [], "gains": {}})
        row["gains"][gain.name] = row["gains"].get(gain.name, 0) + gain.amount
        if id(run) not in row["runs"]:
            row["runs"].append(id(run))
    found = []
    for run in rows:
        if run.gains:
            label = " · ".join([run.name] + run.details)
            found.append({"start": run.start, "label": label, "gains": run.gains})
    totals = []
    for row in sources.values():
        totals.append({"source": row["source"], "runs": len(row["runs"]), "gains": row["gains"]})
    totals.sort(key=lambda row: [row["gains"].get(name, 0) for name in currencies], reverse=True)
    return {"currencies": currencies, "runs": found, "by_source": totals}


def _one_gain(event: dict, current: _Run | None) -> Gain | None:
    """The gain an event is, with the open run's name for one that doesn't say its step."""
    context = []
    if current is not None:
        context.append({"event": "step", "step": current.name, "state": "started"})
    found = gains_with_sources(context + [event])
    return found[0] if found else None
