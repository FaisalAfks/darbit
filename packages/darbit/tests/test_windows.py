"""Finding an app's windows, against a made-up list of windows."""

import pytest

from darbit.platform.backend import Window
from darbit.platform.win32 import windows


@pytest.fixture(autouse=True)
def fake_windows(monkeypatch):
    shown = [
        Window(1, "Anime Dimensions - Roblox - Google Chrome", "chrome.exe", 10),
        Window(2, "Roblox", "RobloxPlayerBeta.exe", 20),
        Window(3, "Notes", "notepad.exe", 30),
    ]
    monkeypatch.setattr(windows, "windows", lambda: shown)
    return shown


def test_a_title_matches_exactly():
    assert [w.handle for w in windows.matching("Roblox")] == [2]


def test_a_title_never_matches_part_of_another_unless_loose(fake_windows):
    fake_windows.pop(1)  # Roblox closed: only the browser tab mentions it
    assert windows.matching("Roblox") == []
    assert [w.handle for w in windows.matching("Roblox", loose=True)] == [1]


def test_a_program_matches_by_file_name_or_path():
    assert [w.handle for w in windows.matching("chrome.exe")] == [1]
    assert [w.handle for w in windows.matching(r"C:\Program Files\Google\Chrome\Application\chrome.exe")] == [1]
