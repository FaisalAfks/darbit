"""What every bot needs, with fakes: keep_trying, a bot's settings as cfg, lag, and counters that start over."""

from datetime import UTC, datetime, timedelta

import numpy as np
import pytest

import darbit as d
from darbit.core.geometry import Region
from darbit.platform import safety
from darbit.runtime import retry
from darbit.runtime import state as state_module


@pytest.fixture(autouse=True)
def quiet(monkeypatch):
    monkeypatch.setattr(d.settings, "log", False)


# ---- keep_trying


def test_a_failure_is_recorded_recovered_from_and_tried_again(monkeypatch):
    events, recovered, tries = [], [], []
    monkeypatch.setattr(retry._record, "recovered", lambda how, why: events.append((how, why)))

    def attempt():
        tries.append(1)
        if len(tries) < 3:
            raise d.Failed("no Start button")

    assert d.keep_trying("Quest", attempt, recover=lambda: recovered.append(1), how="restart") is True
    assert len(tries) == 3 and len(recovered) == 2
    assert events == [("restart", "Quest: no Start button")] * 2


def test_an_interrupt_recovers_with_observers_muted(monkeypatch):
    muted, tries = [], []
    monkeypatch.setattr(retry._record, "recovered", lambda how, why: None)

    def attempt():
        tries.append(1)
        if len(tries) == 1:
            raise d.Interrupted("Game closed")

    def recover():
        muted.append(not safety.interrupt(d.Interrupted("again")))

    assert d.keep_trying("Quest", attempt, recover=recover) is True
    assert muted == [True]


def test_go_on_ends_it_early(monkeypatch):
    monkeypatch.setattr(retry._record, "recovered", lambda how, why: None)
    asked = iter([True, False])

    def attempt():
        raise d.Failed("not yet")

    assert d.keep_trying("Quest", attempt, recover=lambda: None, go_on=lambda: next(asked)) is False


def test_other_errors_are_not_swallowed():
    def attempt():
        raise KeyError("a bug")

    with pytest.raises(KeyError):
        d.keep_trying("Quest", attempt, recover=lambda: None)


# ---- config


SETTINGS = """
[quests]
label = "Quests"

  [quests.enabled]
  type = "bool"
  default = true

  [quests.every_minutes]
  type = "int"
  default = 30
  min = 10
"""


def test_a_bots_settings_read_as_cfg(tmp_path):
    (tmp_path / "settings.toml").write_text(SETTINGS, encoding="utf-8")
    cfg = d.config(tmp_path)
    assert cfg.quests.enabled is True and cfg.quests.every_minutes == 30
    assert (tmp_path / "config.toml").is_file()  # made from the defaults
    (tmp_path / "config.toml").write_text("[quests]\nevery_minutes = 45\n", encoding="utf-8")
    assert d.config(tmp_path).quests.every_minutes == 45


def test_a_bad_value_says_which(tmp_path):
    from darbit.project.settings_schema import SettingsError

    (tmp_path / "settings.toml").write_text(SETTINGS, encoding="utf-8")
    (tmp_path / "config.toml").write_text("[quests]\nevery_minutes = 2\n", encoding="utf-8")
    with pytest.raises(SettingsError, match="every_minutes"):
        d.config(tmp_path)


# ---- lag


def test_lag_makes_searches_and_sleeps_longer(monkeypatch, tmp_path):
    from darbit.core.targets import save
    from darbit.platform import screen

    slept = []
    monkeypatch.setattr(safety, "sleep", lambda seconds: slept.append(seconds))
    d.sleep(2)
    monkeypatch.setattr(d.settings, "lag", 1.5)
    d.sleep(2)
    assert slept == [2, 3.0]

    save(tmp_path / "Start", np.full((8, 8, 3), 200, np.uint8))
    monkeypatch.setattr(d.settings, "images", [tmp_path])
    monkeypatch.setattr(screen, "grab", lambda area=None: (np.zeros((40, 40, 3), np.uint8), Region(0, 0, 40, 40)))
    clock = {"t": 0.0}
    from darbit.runtime import find

    monkeypatch.setattr(find.time, "monotonic", lambda: clock["t"])

    def tick(seconds):
        clock["t"] += max(seconds, 0.2)

    monkeypatch.setattr(find.safety, "sleep", tick)
    assert d.exists("Start", 4) is None
    assert 6 <= clock["t"] < 6.5  # 4 s times 1.5


# ---- counters


@pytest.fixture
def clock(monkeypatch):
    now = {"t": datetime(2026, 11, 2, 6, 0, tzinfo=UTC)}  # a Monday, 06:00 UTC
    monkeypatch.setattr(state_module, "_now", lambda: now["t"])
    monkeypatch.setattr(d.settings, "day_starts", "00:00 UTC")
    return now


def test_a_daily_counter_starts_over_each_day(tmp_path, clock):
    tries = d.State("bot", tmp_path).per_day("boss tries", 3)
    assert tries.left == 3
    assert tries.add() == 2 and tries.add() == 1
    assert d.State("bot", tmp_path).per_day("boss tries", 3).done == 2  # kept across a restart
    assert tries.resets_at() == datetime(2026, 11, 3, 0, 0, tzinfo=UTC)
    clock["t"] += timedelta(days=1)
    assert tries.done == 0 and tries.left == 3


def test_a_weekly_counter_starts_over_at_its_hour(tmp_path, clock):
    s = d.State("bot", tmp_path)
    quests = s.per_week("quests", 70, starts="Mon 07:00 UTC", first=5)
    assert quests.done == 5  # the first time: from where the person said
    quests.add()
    assert quests.resets_at() == datetime(2026, 11, 2, 7, 0, tzinfo=UTC)  # this Monday, an hour from now
    clock["t"] += timedelta(hours=2)
    assert quests.done == 0  # the new week, not `first` again
    assert quests.resets_at() == datetime(2026, 11, 9, 7, 0, tzinfo=UTC)
    quests.set(69)
    assert not quests.full() and quests.add() == 0 and quests.full()


def test_a_week_written_wrongly_says_so(tmp_path):
    with pytest.raises(ValueError, match="Mon 07:00 UTC"):
        d.State("bot", tmp_path).per_week("quests", 70, starts="someday")


def test_a_counter_shows_its_ring(tmp_path, clock, monkeypatch):
    from darbit.runtime import show

    rings = []
    monkeypatch.setattr(show, "progress", lambda label, done, total: rings.append((label, done, total)))
    tries = d.State("bot", tmp_path).per_day("boss tries", 3)
    tries.add(5)
    tries.show("Boss tries today")
    assert rings == [("Boss tries today", 3, 3)]
