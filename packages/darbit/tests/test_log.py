"""The log folder: screenshots saved as JPEG with only the newest kept, and logs and reports kept keep_days."""

import os

import numpy as np

from darbit.core.geometry import Region
from darbit.runtime import log
from darbit.settings import settings


def test_screenshots_are_jpeg_and_the_newest_are_kept(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "logs", tmp_path)
    monkeypatch.setattr(settings, "log", True)
    monkeypatch.setattr(log, "_KEEP_SHOTS", 2)
    monkeypatch.setattr(log.screen, "grab", lambda region=None: (np.zeros((20, 30, 3), np.uint8), Region(0, 0, 30, 20)))
    folder = tmp_path / "screenshots"
    folder.mkdir()
    old = folder / "2026-01-01_00-00-00_old.png"
    old.write_bytes(b"png")
    os.utime(old, (1, 1))  # the oldest file

    first = log.screenshot("first")
    second = log.screenshot("second")

    assert first.endswith(".jpg") and second.endswith(".jpg")
    assert not old.exists()  # trimmed with the JPEGs
    assert sorted(p.suffix for p in folder.iterdir()) == [".jpg", ".jpg"]


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
