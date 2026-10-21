from datetime import UTC, datetime, timedelta

import pytest

import darbit as d
from darbit.runtime import state as module


@pytest.fixture
def clock(monkeypatch):
    now = {"t": datetime(2026, 10, 19, 6, 0, tzinfo=UTC)}  # a Monday, 06:00 UTC
    monkeypatch.setattr(module, "_now", lambda: now["t"])
    return now


def test_values_and_counters_survive_a_restart(tmp_path):
    s = d.State("bot", tmp_path)
    s["team"] = "raid"
    assert s.count("runs") == 1 and s.count("runs", 2) == 3
    again = d.State("bot", tmp_path)
    assert again["team"] == "raid" and again.get("runs") == 3 and again.get("missing", 0) == 0


def test_daily_is_true_once_per_day_from_the_given_hour(tmp_path, clock):
    s = d.State("bot", tmp_path)
    assert s.daily() and not s.daily()
    clock["t"] += timedelta(hours=17)  # 23:00 the same day
    assert not s.daily()
    clock["t"] += timedelta(hours=1)  # midnight
    assert s.daily()
    assert d.State("bot", tmp_path).daily() is False  # remembered after a restart


def test_weekly_from_monday_07_utc(tmp_path, clock):
    s = d.State("sr", tmp_path)
    assert s.weekly(weekday=0, hour_utc=7)  # Monday 06:00 still counts as last week's
    clock["t"] += timedelta(hours=1)  # Monday 07:00: a new week
    assert s.weekly(weekday=0, hour_utc=7)
    clock["t"] += timedelta(days=6, hours=23)  # Monday 06:00 a week later
    assert not s.weekly(weekday=0, hour_utc=7)
    clock["t"] += timedelta(hours=1)
    assert s.weekly(weekday=0, hour_utc=7)


def test_timers(tmp_path, clock):
    s = d.State("sr", tmp_path)
    t = s.timer("speed raid", minutes=30)
    assert t.due()
    t.restart()
    assert not t.due() and t.remaining() == 1800
    clock["t"] += timedelta(minutes=30)
    assert t.due()
    t.restart(5)
    assert d.State("sr", tmp_path).timer("speed raid", 30).remaining() == 300


def test_the_file_is_never_left_half_written(tmp_path):
    s = d.State("bot", tmp_path)
    s["x"] = 1
    assert not list(tmp_path.glob("*.tmp"))
