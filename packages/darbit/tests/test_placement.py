"""Targets placed on the screen as it is now: following their window and resized to the scaling (T22)."""

from types import SimpleNamespace

import cv2
import numpy as np
import pytest

import darbit as d
from darbit.core.geometry import Location, Region
from darbit.core.placement import Place, aspect_changed, placed, ratio
from darbit.core.targets import Target, save
from darbit.platform import screen, windows
from darbit.runtime import find, observe


def smooth_image(seed: int, w: int, h: int) -> np.ndarray:
    """A picture without single-pixel noise, so it still matches itself after resizing."""
    small = np.random.default_rng(seed).integers(0, 255, (h // 4, w // 4, 3), dtype=np.uint8)
    return cv2.resize(small, (w, h), interpolation=cv2.INTER_CUBIC)


BUTTON = smooth_image(2, 40, 28)


# ---- placement on its own


def test_ratio_uses_the_window_width_when_it_was_saved():
    target = Target(scale=1.5, window=(800, 600), origin=(0, 0))
    assert ratio(target, Place(Region(0, 0, 1200, 900), 1.0)) == 1.5  # not also the scaling
    assert ratio(target, Place(None, 1.0)) == pytest.approx(1 / 1.5)
    assert ratio(Target(), Place(Region(0, 0, 100, 100), 2.0)) == 1.0


def test_placed_moves_and_scales_everything_with_the_window():
    target = Target(
        region=Region(110, 220, 50, 40),
        location=Location(130, 230),
        offset=(4, -2),
        window=(800, 600),
        origin=(100, 200),
        _pixels=BUTTON,
    )
    now = placed(target, Place(Region(500, 300, 1600, 1200)))
    assert now.region == Region(520, 340, 100, 80)
    assert now.location == Location(560, 360)
    assert now.offset == (8, -4)
    assert now.pixels.shape[:2] == (56, 80)
    assert placed(now, Place(Region(0, 0, 50, 50), 3.0), extra=1.1) is now  # placing again changes nothing


def test_placed_leaves_old_targets_alone():
    old = Target(region=Region(1, 2, 3, 4), scale=1.5, _pixels=BUTTON)
    assert placed(old, Place(Region(500, 500, 100, 100), 1.5)) is old
    assert placed(old, Place(None, None)) is old


def test_scale_only_grows_the_region_around_its_centre():
    target = Target(region=Region(100, 100, 40, 20), scale=1.0, _pixels=BUTTON)
    now = placed(target, Place(None, 1.5))
    assert now.region == Region(90, 95, 60, 30)
    assert now.pixels.shape[:2] == (42, 60)


def test_aspect_change_is_noticed():
    target = Target(window=(800, 600), origin=(0, 0))
    assert not aspect_changed(target, Place(Region(0, 0, 1600, 1200)))
    assert aspect_changed(target, Place(Region(0, 0, 1600, 900)))


# ---- searching a fake screen


def fake_scale(value: float):
    def scale_at(x, y):
        return value

    return scale_at


def game_at(monkeypatch, area: Region | None) -> None:
    """The game window's content area, or None when it isn't open."""

    def matching(name, loose=False):
        if area is None:
            return []
        return [SimpleNamespace(handle=1)]

    def region(handle):
        return area

    monkeypatch.setattr(windows, "matching", matching)
    monkeypatch.setattr(windows, "region", region)


@pytest.fixture
def draw(tmp_path, monkeypatch):
    """A fake 1200x900 screen at 150%; returns a function that draws the button on it."""
    shown = {"pixels": smooth_image(1, 1200, 900)}

    def grab(region=None):
        whole = Region(0, 0, 1200, 900)
        region = whole if region is None else region.intersect(whole)
        if region is None:
            return np.zeros((0, 0, 3), np.uint8), Region(0, 0, 0, 0)
        return shown["pixels"][region.y : region.bottom, region.x : region.right].copy(), region

    monkeypatch.setattr(screen, "grab", grab)
    monkeypatch.setattr(screen, "scale_at", fake_scale(1.5))
    monkeypatch.setattr(d.settings, "images", [tmp_path])
    monkeypatch.setattr(d.settings, "log", False)
    monkeypatch.setattr(d.settings, "similarity", 0.9)
    monkeypatch.setattr(d.settings, "window", "Game")
    monkeypatch.setattr(find, "_adjust", {})
    monkeypatch.setattr(find, "_tried", {})
    monkeypatch.setattr(find, "_warned", set())
    game_at(monkeypatch, None)

    def draw_button(at, size=1.0):
        image = BUTTON
        if size != 1.0:
            w, h = round(BUTTON.shape[1] * size), round(BUTTON.shape[0] * size)
            image = cv2.resize(BUTTON, (w, h), interpolation=cv2.INTER_LINEAR)
        x, y = at
        shown["pixels"][y : y + image.shape[0], x : x + image.shape[1]] = image

    return draw_button


def test_an_old_target_is_found_where_it_always_was(draw, tmp_path, monkeypatch):
    save(tmp_path / "Old", BUTTON, region=[0, 0, 600, 400], scale=1.5)
    game_at(monkeypatch, Region(300, 300, 800, 500))  # the window is set and open
    draw((100, 50))
    found = d.exists("Old")
    assert (found.x, found.y, found.w, found.h) == (100, 50, 40, 28)


def test_a_target_follows_its_window(draw, tmp_path, monkeypatch):
    monkeypatch.setattr(d.settings, "space", "window")
    save(tmp_path / "Play", BUTTON, region=[10, 10, 100, 60], window=[400, 300], origin=[0, 0])
    game_at(monkeypatch, Region(500, 400, 400, 300))  # moved, same size
    draw((530, 425))
    found = d.exists("Play")
    assert (found.x, found.y) == (530, 425)


def test_a_target_grows_with_its_window(draw, tmp_path, monkeypatch):
    monkeypatch.setattr(d.settings, "space", "window")
    save(tmp_path / "Play", BUTTON, region=[10, 10, 100, 60], offset=[5, 0], window=[400, 300], origin=[0, 0])
    game_at(monkeypatch, Region(100, 100, 800, 600))  # moved and twice as big
    draw((160, 150), size=2.0)
    found = d.exists("Play")
    assert (found.x, found.y, found.w, found.h) == (160, 150, 80, 56)
    assert found.score > 0.95
    assert found.point == Location(160 + 40 + 10, 150 + 28)


def test_in_window_space_a_target_without_a_region_is_searched_only_in_the_window(draw, tmp_path, monkeypatch):
    monkeypatch.setattr(d.settings, "space", "window")
    save(tmp_path / "Play", BUTTON, window=[400, 300], origin=[0, 0])
    game_at(monkeypatch, Region(500, 400, 400, 300))
    draw((30, 20))  # a copy outside the window: not this window's button
    assert not d.exists("Play")
    draw((530, 425))
    assert d.exists("Play").x == 530


def test_in_screen_space_a_target_stays_where_it_was_taken(draw, tmp_path, monkeypatch):
    save(tmp_path / "Play", BUTTON, region=[10, 10, 100, 60], window=[400, 300], origin=[0, 0])
    game_at(monkeypatch, Region(500, 400, 400, 300))  # the window moved, but places are screen pixels
    draw((530, 425))
    assert not d.exists("Play")  # searched in its region as taken, top left
    draw((30, 20))
    assert d.exists("Play")


def test_without_its_window_open_a_target_stays_put(draw, tmp_path):
    save(tmp_path / "Play", BUTTON, region=[10, 10, 100, 60], window=[400, 300], origin=[0, 0])
    draw((30, 20))
    found = d.exists("Play")
    assert (found.x, found.y) == (30, 20)


def test_a_target_is_resized_to_the_scaling(draw, tmp_path):
    save(tmp_path / "Play", BUTTON, scale=1.0)  # taken at 100%, the screen is 150%
    draw((300, 200), size=1.5)
    found = d.exists("Play")
    assert (found.x, found.y, found.w, found.h) == (300, 200, 60, 42)


def test_nearby_sizes_are_tried_once_and_kept(draw, tmp_path, monkeypatch):
    monkeypatch.setattr(d.settings, "similarity", 0.98)
    save(tmp_path / "Play", BUTTON, scale=1.0)
    draw((300, 200), size=1.5 * 1.1)  # bigger than the scaling says
    found = d.exists("Play")
    assert found is not None
    assert find._adjust == {"Play": 1.1}
    assert (found.w, found.h) == (66, 46)

    tries = []

    def counted(*args):
        tries.append(args)

    monkeypatch.setattr(find, "_nearby_sizes", counted)
    assert d.exists("Play") is not None
    assert tries == []  # found at the kept size straight away


def test_not_found_at_any_size_is_tried_again_a_minute_later(draw, tmp_path, monkeypatch):
    save(tmp_path / "Play", BUTTON, scale=1.0)
    looks = []
    real_look = find._look

    def counted(chosen, region):
        looks.append(1)
        return real_look(chosen, region)

    clock = [1000.0]

    def monotonic():
        return clock[0]

    monkeypatch.setattr(find, "_look", counted)
    monkeypatch.setattr(find.time, "monotonic", monotonic)
    assert d.exists("Play") is None
    assert len(looks) == 1 + 4  # one look, then the four nearby sizes
    looks.clear()
    clock[0] += 30
    assert d.exists("Play") is None
    assert len(looks) == 1  # not again within the minute
    looks.clear()
    clock[0] += 31
    draw((300, 200), size=1.5 * 1.1)  # now it shows, a bit bigger than expected
    monkeypatch.setattr(d.settings, "similarity", 0.98)
    assert d.exists("Play") is not None
    assert find._adjust == {"Play": 1.1}


def test_a_minimised_window_leaves_targets_as_taken(draw, tmp_path, monkeypatch):
    save(tmp_path / "Play", BUTTON, region=[10, 10, 100, 60], window=[400, 300], origin=[0, 0])
    game_at(monkeypatch, Region(-32000, -32000, 0, 0))  # what Windows reports for a minimised window
    draw((30, 20))
    found = d.exists("Play")
    assert (found.x, found.y, found.w, found.h) == (30, 20, 40, 28)
    target = Target(window=(400, 300), origin=(0, 0))
    assert not aspect_changed(target, Place(Region(0, 0, 0, 0)))


def test_observers_follow_the_window(draw, tmp_path, monkeypatch):
    save(tmp_path / "Lost", BUTTON, window=[400, 300], origin=[0, 0])
    target = find.target("Lost")
    watcher = observe.Observer("Lost", target=target)
    draw((700, 500))
    game_at(monkeypatch, Region(0, 0, 400, 300))
    hit = observe._look(watcher, screen.grab(), find.where_now([target]))
    assert hit is not None
    assert (hit.x, hit.y) == (700, 500)
