"""The SikuliX-style API: Pattern, Region, Screen and App, and loaded pictures kept until their files change."""

import os

import cv2
import numpy as np
import pytest

import darbit as d
from darbit.core import geometry, targets
from darbit.core.targets import load, save
from darbit.platform import screen, windows


@pytest.fixture
def fake(tmp_path, monkeypatch):
    rng = np.random.default_rng(1)
    shown = rng.integers(0, 255, (400, 600, 3), dtype=np.uint8)
    button = np.random.default_rng(2).integers(0, 255, (20, 30, 3), dtype=np.uint8)
    shown[50:70, 100:130] = button
    save(tmp_path / "Gui.Play", button, similarity=0.95, offset=[1, 1])

    def grab(region=None):
        whole = geometry.Region(0, 0, 600, 400)
        region = whole if region is None else region.intersect(whole)
        if region is None:
            return np.zeros((0, 0, 3), np.uint8), geometry.Region(0, 0, 0, 0)
        return shown[region.y : region.bottom, region.x : region.right].copy(), region

    monkeypatch.setattr(screen, "grab", grab)
    monkeypatch.setattr(d.settings, "images", [tmp_path])
    monkeypatch.setattr(d.settings, "log", False)
    return tmp_path


def test_pattern_settings_go_over_the_pictures_own(fake):
    plain = load("Gui.Play", [fake])
    assert plain.similarity == 0.95 and plain.offset == (1, 1)
    changed = load(d.Pattern("Gui.Play").similar(0.6).offset(5, -5).options(fast=True), [fake])
    assert changed.similarity == 0.6 and changed.offset == (5, -5) and changed.match == {"fast": True}
    assert load(d.Pattern("Gui.Play").exact(), [fake]).similarity == targets.EXACT


def test_a_pattern_is_found_and_clicked_where_its_offset_says(fake):
    found = d.exists(d.Pattern("Gui.Play").offset(10, 0))
    assert (found.x, found.y) == (100, 50)
    assert found.point == d.Location(125, 60)


def test_a_region_searches_only_inside_itself(fake):
    assert d.Region(300, 0, 300, 400).exists("Gui.Play") is None
    left = d.Region(0, 0, 300, 400)
    assert (left.exists("Gui.Play").x, left.find("Gui.Play", timeout=0).y) == (100, 50)
    assert len(left.find_all("Gui.Play")) == 1
    assert left.vanish("Gui.Play", timeout=0) is False


def test_a_region_of_a_match_and_regions_compare_by_their_numbers(fake):
    found = d.exists("Gui.Play")
    around = d.Region.of(found)
    assert around == geometry.Region(100, 50, 30, 20)
    assert around.grow(5).exists("Gui.Play") is not None
    assert isinstance(around.grow(5), d.Region)
    assert len({around, geometry.Region(100, 50, 30, 20)}) == 1


def test_screen_is_the_desktop_or_one_monitor(monkeypatch):
    monkeypatch.setattr(screen, "desktop", lambda: geometry.Region(0, 0, 3840, 1080))
    monkeypatch.setattr(
        screen, "monitors", lambda: [geometry.Region(0, 0, 1920, 1080), geometry.Region(1920, 0, 1920, 1080)]
    )
    assert d.Screen() == d.Region(0, 0, 3840, 1080)
    assert d.Screen(1).x == 1920 and isinstance(d.Screen(1), d.Region)


def test_an_apps_window_is_a_region(monkeypatch):
    monkeypatch.setattr(
        windows,
        "matching",
        lambda app, loose=False: [windows.Window(7, "Roblox", "RobloxPlayerBeta.exe", 1)] if app == "Roblox" else [],
    )
    monkeypatch.setattr(windows, "region", lambda handle: geometry.Region(10, 20, 800, 600))
    game = d.App("Roblox").window
    assert isinstance(game, d.Region) and game == d.Region(10, 20, 800, 600)
    assert d.App("Roblox").running and not d.App("Notepad").running
    assert d.App("Notepad").window is None


def test_a_loaded_picture_is_kept_until_its_file_changes(fake, monkeypatch):
    first = load("Gui.Play", [fake])
    assert load("Gui.Play", [fake]) is first
    monkeypatch.setattr(targets, "CHECK_EVERY", 0)
    assert load("Gui.Play", [fake]) is first  # checked, nothing changed
    picture = fake / "Gui.Play.png"
    _, data = cv2.imencode(".png", np.zeros((10, 10, 3), np.uint8))
    picture.write_bytes(data.tobytes())  # taken again by another program
    later = picture.stat().st_mtime + 5
    os.utime(picture, (later, later))
    again = load("Gui.Play", [fake])
    assert again is not first and again.pixels.shape == (10, 10, 3)
