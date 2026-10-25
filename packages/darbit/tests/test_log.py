"""Screenshots in the log folder: saved as JPEG, and only the newest kept (old PNGs included)."""

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
