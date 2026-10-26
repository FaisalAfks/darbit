"""The Studio window opens where it was left, but never off every screen; its place is saved once it stops."""

import time

import pytest

from darbit import paths
from darbit.desktop import studio
from darbit.server import hub, ui_settings

SCREENS = [(0, 0, 1920, 1080), (1920, 0, 2560, 1440)]


def test_a_saved_place_on_a_screen_is_used():
    saved = {"x": 2000, "y": 100, "width": 1280, "height": 860}
    assert studio.saved_place(saved, SCREENS) == saved


@pytest.mark.parametrize(
    "saved",
    [
        None,
        "nonsense",
        {"x": 5000, "y": 100, "width": 1280, "height": 860},  # its screen was unplugged
        {"x": 100, "y": -500, "width": 1280, "height": 860},  # title bar above every screen
        {"x": 100, "y": 100, "width": 300, "height": 200},  # smaller than the Studio can be
        {"x": "a", "y": 100, "width": 1280, "height": 860},
        {"y": 100, "width": 1280, "height": 860},
    ],
)
def test_a_lost_or_broken_place_is_ignored(saved):
    assert studio.saved_place(saved, SCREENS) is None


def test_the_place_is_saved_after_moving_stops(tmp_path, monkeypatch):
    def config_dir():
        return tmp_path

    monkeypatch.setattr(paths, "config_dir", config_dir)
    monkeypatch.setattr(studio, "SAVE_AFTER", 0.05)
    place = studio.Place({})
    place.moved(-32000, -32000)  # minimised: ignored
    place.moved(100, 120)
    place.resized(1300, 900)
    place.resized(160, 40)  # minimised: ignored
    time.sleep(0.3)
    assert ui_settings.get(studio.PLACE) == {"x": 100, "y": 120, "width": 1300, "height": 900}


def test_no_running_bots_to_stop():
    assert hub.running() == []
    hub.stop_all()
