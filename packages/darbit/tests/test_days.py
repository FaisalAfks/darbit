"""A bot's day: when it starts (`[settings] day_starts`), and which day a moment belongs to."""

from datetime import UTC, datetime, timedelta, timezone

import pytest

from darbit import days
from darbit.project.manifest import ProjectError, load
from darbit.server import dashboard


def test_day_starts_reads_a_time_or_a_utc_time():
    assert days.parse("03:00") == days.DayStart(3, 0, False)
    assert days.parse("3:30") == days.DayStart(3, 30, False)
    assert days.parse("00:00 UTC") == days.DayStart(0, 0, True)
    assert days.parse(None) == days.DayStart()  # midnight
    for wrong in ("25:00", "3:61", "noon", "03:00 GMT+3"):
        with pytest.raises(ValueError, match="day_starts"):
            days.parse(wrong)


def test_a_moment_before_the_day_starts_is_the_day_before():
    starts = days.parse("03:00")
    assert days.day_of(datetime(2026, 11, 2, 2, 59), starts) == "2026-11-01"
    assert days.day_of(datetime(2026, 11, 2, 3, 0), starts) == "2026-11-02"
    assert days.day_of(datetime(2026, 11, 2, 0, 30), days.DayStart()) == "2026-11-02"


def test_a_utc_day_is_the_same_wherever_the_pc_is():
    riyadh = timezone(timedelta(hours=3))
    starts = days.parse("00:00 UTC")
    assert days.day_of(datetime(2026, 11, 2, 2, 30, tzinfo=riyadh), starts) == "2026-11-01"  # 23:30 UTC
    assert days.day_of(datetime(2026, 11, 2, 3, 30, tzinfo=riyadh), starts) == "2026-11-02"
    assert days.day_of(datetime(2026, 11, 2, 0, 0, tzinfo=UTC), starts) == "2026-11-02"


def test_a_bot_names_its_day_start_in_darbit_toml(tmp_path):
    (tmp_path / "darbit.toml").write_text('[bot]\nname = "b"\n[settings]\nday_starts = "03:00"\n', encoding="utf-8")
    project = load(tmp_path)
    assert dashboard.today(project, datetime(2026, 11, 2, 1, 0)) == "2026-11-01"
    (tmp_path / "darbit.toml").write_text('[bot]\nname = "b"\n[settings]\nday_starts = "noon"\n', encoding="utf-8")
    with pytest.raises(ProjectError, match="day_starts"):
        load(tmp_path)


def test_the_run_report_keeps_one_file_for_a_day_past_midnight(tmp_path, monkeypatch):
    from darbit.runtime import log
    from darbit.settings import settings

    monkeypatch.setattr(settings, "logs", tmp_path)
    monkeypatch.setattr(settings, "day_starts", "03:00")
    monkeypatch.setattr(log.days, "today", lambda start: days.day_of(datetime(2026, 11, 2, 1, 0), start))
    log.record("step", step="AFK", state="started")
    assert (tmp_path / "report-2026-11-01.jsonl").is_file()  # 01:00 belongs to the day before
