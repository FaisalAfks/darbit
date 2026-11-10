"""The log folder: screenshots saved as JPEG with only the newest kept, and logs and reports kept keep_days."""

import os

import numpy as np
import pytest

import darbit as d
from darbit.core.geometry import Region
from darbit.runtime import log
from darbit.settings import settings


@pytest.fixture
def shots(tmp_path, monkeypatch):
    """Screenshots on: saved into tmp_path, of a small black screen."""
    monkeypatch.setattr(settings, "logs", tmp_path)
    monkeypatch.setattr(settings, "log", True)
    monkeypatch.setattr(log.screen, "grab", lambda region=None: (np.zeros((20, 30, 3), np.uint8), Region(0, 0, 30, 20)))
    return tmp_path


def test_screenshots_are_jpeg_and_the_newest_are_kept(shots):
    folder = shots / "screenshots"
    folder.mkdir()
    old = folder / "2026-01-01_00-00-00_old.png"
    old.write_bytes(b"png")
    os.utime(old, (1, 1))  # the oldest file

    first = log.screenshot("first", keep=2)
    second = log.screenshot("second", keep=2)

    assert first.endswith(".jpg") and second.endswith(".jpg") and "/" not in first
    assert not old.exists()  # trimmed with the JPEGs
    assert sorted(p.suffix for p in folder.iterdir()) == [".jpg", ".jpg"]
    assert log.KEEP_SHOTS == 200  # by default, in logs/screenshots


def test_a_screenshot_goes_into_its_own_folder_with_its_own_limit(shots):
    failures = shots / "screenshots"
    failures.mkdir()
    failure = failures / "2026-01-01_00-00-00_failed.jpg"
    failure.write_bytes(b"jpg")
    os.utime(failure, (1, 1))  # older than everything here
    rewards = shots / "rewards"
    rewards.mkdir()
    old = rewards / "2026-01-01_00-00-00_old.jpg"
    old.write_bytes(b"jpg")
    os.utime(old, (1, 1))

    name = d.screenshot("raid", folder="rewards", keep=1)

    assert name.startswith("rewards/") and name.endswith("_raid.jpg")  # a record's shot names the file in logs
    assert (shots / name).is_file() and not old.exists()  # the newest one kept there
    assert failure.exists()  # the failure shots are another folder's
    assert d.screenshot("deeper", folder="rewards/raid").startswith("rewards/raid/")


@pytest.mark.parametrize(
    "folder",
    [
        "",
        ".",
        "..",
        "../elsewhere",
        "rewards/../..",
        "/tmp",
        "//server/share",
        r"\\server\share",
        "C:/shots",
        "C:shots",
    ],
)
def test_a_folder_outside_logs_is_a_mistake(shots, folder):
    with pytest.raises(ValueError, match="a folder inside logs"):
        log.screenshot("x", folder=folder)
    assert list(shots.iterdir()) == []


def test_keeping_none_is_a_mistake(shots):
    with pytest.raises(ValueError, match="keeps at least the one just taken"):
        log.screenshot("x", folder="rewards", keep=0)


def test_old_logs_and_reports_go_when_the_bot_starts_writing(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "logs", tmp_path)
    monkeypatch.setattr(settings, "log", True)
    monkeypatch.setattr(settings, "keep_days", 1)
    monkeypatch.setattr(log, "_tidied", None)
    monkeypatch.setattr(log, "_today", lambda: "2026-11-09")
    for day in ("2026-11-07", "2026-11-08"):
        (tmp_path / f"report-{day}.jsonl").write_text("{}\n", encoding="utf-8")
        (tmp_path / f"{day}.log").write_text("a line\n", encoding="utf-8")
    (tmp_path / "studio-output.log").write_text("output\n", encoding="utf-8")

    log.record("gain", name="Fish", amount=1)

    assert sorted(path.name for path in tmp_path.iterdir()) == [
        "2026-11-08.log",  # yesterday's stays
        "report-2026-11-08.jsonl",
        "report-2026-11-09.jsonl",
        "studio-output.log",  # not a day's file
    ]
    (tmp_path / "report-2026-11-01.jsonl").write_text("{}\n", encoding="utf-8")
    log.record("gain", name="Fish", amount=1)
    assert (tmp_path / "report-2026-11-01.jsonl").exists()  # once a day, not on every line
