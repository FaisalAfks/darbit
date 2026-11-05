"""Saved values that survive restarts: counters, daily and weekly resets, timers.

    s = d.State("quests")                  # state/quests.json next to the script
    if s.weekly(weekday=0, hour_utc=7):       # True once each week, from Monday 07:00 UTC
        s["done"] = 0
    s.count("done")                           # add 1 and save
    quest = s.timer("daily quest", minutes=30)
    if quest.due():
        ...
        quest.restart()

Counters that start over by themselves each day (the bot's `day_starts`) or each week:

    tries = s.per_day("boss tries", 3)          # 3 a day
    if tries.left:
        tries.add()
    quests = s.per_week("quests", 70, starts="Mon 07:00 UTC")
    quests.show("Quests this week")             # a ring on the Overview

Every change is saved straight away, so a crash or the stop hotkey loses nothing.
"""

import json
import os
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from .. import days
from ..settings import settings

PERIODS = "_periods"  # where the daily and weekly resets remember the last period they saw
TIMERS = "_timers"
COUNTERS = "_counters"
WEEKDAYS = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]


def _now() -> datetime:
    return datetime.now(UTC)


class Timer:
    """Something due every few minutes. Its next due time is kept in the State."""

    def __init__(self, state: "State", name: str, minutes: float) -> None:
        self.state, self.name, self.minutes = state, name, minutes

    @property
    def due_at(self) -> float:
        return float(self.state.data.get(TIMERS, {}).get(self.name, 0))

    def due(self) -> bool:
        return _now().timestamp() >= self.due_at

    def remaining(self) -> float:
        """Seconds until it's due, 0 if it already is."""
        return max(0.0, self.due_at - _now().timestamp())

    def restart(self, minutes: float | None = None) -> None:
        """Due again `minutes` from now (its own interval by default)."""
        timers = self.state.data.setdefault(TIMERS, {})
        timers[self.name] = _now().timestamp() + 60 * (self.minutes if minutes is None else minutes)
        self.state.save()

    def clear(self) -> None:
        """Due now."""
        self.state.data.setdefault(TIMERS, {})[self.name] = 0
        self.state.save()


def _week_start(text: str) -> tuple[int, days.DayStart]:
    """ "Mon 07:00 UTC" -> (0, 07:00 UTC). A week that names no time starts at the bot's day start."""
    words = text.strip().split(maxsplit=1)
    if not words or words[0][:3].lower() not in WEEKDAYS:
        raise ValueError(f'a week starts on a day and a time, like "Mon 07:00 UTC", not "{text}"')
    weekday = WEEKDAYS.index(words[0][:3].lower())
    if len(words) == 1:
        return weekday, days.parse(settings.day_starts)
    return weekday, days.parse(words[1])


def _day_begins(start: days.DayStart, now: datetime) -> datetime:
    """When the day `now` is in began (aware, in UTC or this PC's zone)."""
    moment = now.astimezone(UTC) if start.utc else now.astimezone()
    begun = moment.replace(hour=start.hour, minute=start.minute, second=0, microsecond=0)
    if begun > moment:
        begun -= timedelta(days=1)
    return begun


class Counter:
    """How many of something are done this day or week; it starts over by itself when the next one begins.
    Kept in the State, under its name."""

    def __init__(self, state: "State", name: str, total: int, week: str | None, first: int) -> None:
        self.state, self.name, self.total, self.week = state, name, total, week
        saved = state.data.setdefault(COUNTERS, {})
        if name not in saved:
            saved[name] = {"period": self._period(), "done": first}
            state.save()

    def _begins(self) -> datetime:
        """When the current day or week began."""
        now = _now()
        if self.week is None:
            return _day_begins(days.parse(settings.day_starts), now)
        weekday, start = _week_start(self.week)
        begun = _day_begins(start, now)
        return begun - timedelta(days=(begun.weekday() - weekday) % 7)

    def _period(self) -> str:
        return self._begins().strftime("%Y-%m-%d %H:%M")

    def _saved(self) -> dict:
        entry = self.state.data.setdefault(COUNTERS, {}).setdefault(self.name, {"period": "", "done": 0})
        if entry.get("period") != self._period():
            entry["period"], entry["done"] = self._period(), 0
            self.state.save()
        return entry

    @property
    def done(self) -> int:
        return int(self._saved()["done"])

    @property
    def left(self) -> int:
        return max(self.total - self.done, 0)

    def full(self) -> bool:
        return self.done >= self.total

    def add(self, by: int = 1) -> int:
        """Count `by` more done; returns how many are left."""
        self._saved()["done"] = self.done + by
        self.state.save()
        return self.left

    def set(self, done: int) -> None:
        self._saved()["done"] = done
        self.state.save()

    def resets_at(self) -> datetime:
        """When it next starts over."""
        return self._begins() + timedelta(days=1 if self.week is None else 7)

    def show(self, label: str) -> None:
        """Its ring on darbit Studio's Overview: done of total."""
        from .show import progress

        progress(label, min(self.done, self.total), self.total)


class State:
    """A small JSON file of values, in the state folder (settings.state)."""

    def __init__(self, name: str, folder: Path | None = None) -> None:
        self.name = name
        self.path = (folder or settings.state) / f"{name}.json"
        self.data: dict[str, Any] = {}
        if self.path.is_file():
            self.data = json.loads(self.path.read_text(encoding="utf-8"))

    # ----------------------------------------------------------------- values

    def get(self, key: str, default: Any = None) -> Any:
        return self.data.get(key, default)

    def set(self, key: str, value: Any) -> None:
        self.data[key] = value
        self.save()

    def __getitem__(self, key: str) -> Any:
        return self.data[key]

    def __setitem__(self, key: str, value: Any) -> None:
        self.set(key, value)

    def __contains__(self, key: str) -> bool:
        return key in self.data

    def count(self, key: str, by: int = 1) -> int:
        """Add to a counter and return it."""
        self.data[key] = int(self.data.get(key, 0)) + by
        self.save()
        return self.data[key]

    # ---------------------------------------------------------------- periods

    def _new_period(self, kind: str, period: str) -> bool:
        periods = self.data.setdefault(PERIODS, {})
        if periods.get(kind) == period:
            return False
        periods[kind] = period
        self.save()
        return True

    def daily(self, hour_utc: int = 0, name: str = "daily") -> bool:
        """True the first time it's asked in each day, days starting at `hour_utc` UTC."""
        start = _now() - timedelta(hours=hour_utc)
        return self._new_period(name, start.date().isoformat())

    def weekly(self, weekday: int = 0, hour_utc: int = 0, name: str = "weekly") -> bool:
        """True the first time it's asked in each week, weeks starting on `weekday` (Monday 0) at `hour_utc` UTC."""
        start = _now() - timedelta(hours=hour_utc)
        week_start = start - timedelta(days=(start.weekday() - weekday) % 7)
        return self._new_period(name, week_start.date().isoformat())

    # ----------------------------------------------------------------- timers

    def timer(self, name: str, minutes: float) -> Timer:
        return Timer(self, name, minutes)

    def per_day(self, name: str, total: int, first: int = 0) -> Counter:
        """A counter of `total` a day, days starting at the bot's `day_starts`. `first` is how many count as done
        the very first time, before anything was saved."""
        return Counter(self, name, total, None, first)

    def per_week(self, name: str, total: int, starts: str = "Mon", first: int = 0) -> Counter:
        """A counter of `total` a week, weeks starting at `starts`: "Mon" (at the day start) or "Mon 07:00 UTC"."""
        _week_start(starts)  # a mistake shows now, not later
        return Counter(self, name, total, starts, first)

    # ------------------------------------------------------------------ saving

    def save(self) -> None:
        """Write the file whole, through a temporary file so a crash never leaves it half written."""
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_name(self.path.name + ".tmp")
        temporary.write_text(json.dumps(self.data, indent=2, sort_keys=True), encoding="utf-8")
        os.replace(temporary, self.path)
