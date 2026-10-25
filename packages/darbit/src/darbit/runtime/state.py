"""Saved values that survive restarts: counters, daily and weekly resets, timers.

    s = d.State("speedraid")                  # state/speedraid.json next to the script
    if s.weekly(weekday=0, hour_utc=7):       # True once each week, from Monday 07:00 UTC
        s["done"] = 0
    s.count("done")                           # add 1 and save
    raid = s.timer("speed raid", minutes=30)
    if raid.due():
        ...
        raid.restart()

Every change is saved straight away, so a crash or the stop hotkey loses nothing.
"""

from __future__ import annotations

import json
import os
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from ..settings import settings

PERIODS = "_periods"  # where the daily and weekly resets remember the last period they saw
TIMERS = "_timers"


def _now() -> datetime:
    return datetime.now(UTC)


class Timer:
    """Something due every few minutes. Its next due time is kept in the State."""

    def __init__(self, state: State, name: str, minutes: float) -> None:
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

    # ------------------------------------------------------------------ saving

    def save(self) -> None:
        """Write the file whole, through a temporary file so a crash never leaves it half written."""
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_name(self.path.name + ".tmp")
        temporary.write_text(json.dumps(self.data, indent=2, sort_keys=True), encoding="utf-8")
        os.replace(temporary, self.path)
