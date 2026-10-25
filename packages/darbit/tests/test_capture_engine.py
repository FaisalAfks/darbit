"""The capture engine on synthetic screens: click to select at every size, and snapping."""

import json
import time
from pathlib import Path

import cv2
import numpy as np
import pytest

from darbit.capture.engine import candidates, lines, pick, prepare, snap_box
from darbit.core.geometry import Region

CASES = Path(__file__).parent / "data" / "capture" / "snap_cases.json"


def _screen(w: int = 2560, h: int = 1600) -> tuple[np.ndarray, dict[str, Region]]:
    """A game-like screen: a noisy background, a big window with a 3 px border, a list panel inside it,
    and a button with letters on it."""
    rng = np.random.default_rng(1)
    shot = rng.integers(20, 60, (h, w, 3), dtype=np.uint8)  # texture: no straight lines
    shot = cv2.GaussianBlur(shot, (5, 5), 0)
    parts = {
        "window": Region(300, 150, 1900, 1200),  # bigger than the old 900x600 search area
        "panel": Region(400, 300, 1000, 800),
        "button": Region(1600, 1150, 420, 94),
    }
    for name, colour, thick, inside in (
        ("window", (200, 120, 110), 3, (70, 40, 45)),
        ("panel", (160, 160, 160), 2, (90, 60, 60)),
    ):
        r = parts[name]  # the border is inside the region, `thick` pixels wide
        shot[r.y : r.bottom, r.x : r.right] = colour
        shot[r.y + thick : r.bottom - thick, r.x + thick : r.right - thick] = inside
    b = parts["button"]
    shot[b.y : b.bottom, b.x : b.right] = (90, 220, 80)
    for i in range(5):  # dark "letters" on the button
        shot[b.y + 30 : b.y + 64, b.x + 120 + i * 40 : b.x + 140 + i * 40] = (20, 80, 20)
    return shot, parts


@pytest.fixture(scope="module")
def screen():
    shot, parts = _screen()
    return prepare(shot), parts


def _near(a: Region, b: Region, tolerance: int = 6) -> bool:
    return all(abs(p - q) <= tolerance for p, q in ((a.x, b.x), (a.y, b.y), (a.right, b.right), (a.bottom, b.bottom)))


def test_a_click_on_a_button_selects_the_button_then_bigger_things(screen):
    prep, parts = screen
    boxes = candidates(prep, parts["button"].x + 20, parts["button"].y + 15, "image")
    assert boxes[pick(boxes)] == parts["button"]  # exactly
    assert parts["window"] in boxes  # clicking again reaches the window, on its border
    assert boxes[-1] == Region(0, 0, 2560, 1600)  # and ends with the screen
    assert [b.w * b.h for b in boxes] == sorted(b.w * b.h for b in boxes)


def test_a_click_on_a_letter_still_reaches_the_button(screen):
    prep, parts = screen
    b = parts["button"]
    boxes = candidates(prep, b.x + 130, b.y + 45, "image")
    assert boxes[0].w < 40  # the letter is there, for "smaller"
    assert boxes[pick(boxes)] == b  # but a click starts on the button


def test_region_clicks_select_windows_bigger_than_the_old_limit(screen):
    prep, parts = screen
    boxes = candidates(prep, parts["panel"].x + 50, parts["panel"].y + 50, "region")
    assert boxes[0] == parts["panel"]
    assert parts["window"] in boxes[:3]
    assert all(b.w >= 80 and b.h >= 60 for b in boxes)


def test_lines_find_borders_but_not_texture(screen):
    prep, parts = screen
    w = parts["window"]
    assert any(x == w.x and y0 <= w.y + 10 and y1 >= w.bottom - 10 for x, y0, y1 in prep.lines["v"])
    assert any(x == w.x + 3 for x, _, _ in prep.lines["v"])  # and its inner side
    noise = cv2.GaussianBlur(np.random.default_rng(2).integers(20, 60, (400, 400), dtype=np.uint8), (5, 5), 0)
    found = lines(noise)
    assert not [s for s in found["h"] + found["v"] if s[2] - s[1] >= 40]


def test_snap_cases():
    for case in json.loads(CASES.read_text(encoding="utf-8")):
        found = {"h": [tuple(s) for s in case["lines"]["h"]], "v": [tuple(s) for s in case["lines"]["v"]]}
        box, guides = snap_box(found, Region(*case["box"]), set(case["moving"]), border=case.get("border", "include"))
        assert [box.x, box.y, box.w, box.h] == case["expect"], case["name"]
        assert len(guides) == case["guides"], case["name"]


def test_snapping_the_real_borders(screen):
    prep, parts = screen
    w = parts["window"]
    rough = Region(w.x + 4, w.y - 3, w.w - 9, w.h + 5)  # a box drawn a few pixels off
    box, guides = snap_box(prep.lines, rough, {"left", "top", "right", "bottom"})
    assert box == w and len(guides) == 4  # exactly the window, border included
    inner, _ = snap_box(prep.lines, rough, {"left", "top", "right", "bottom"}, border="exclude")
    assert inner == Region(w.x + 3, w.y + 3, w.w - 6, w.h - 6)


def test_prepare_is_fast_enough():
    shot, _ = _screen()
    started = time.perf_counter()
    prepare(shot)
    took = time.perf_counter() - started
    print(f"prepare 2560x1600: {took * 1000:.0f} ms")
    assert took < 1.0  # the target is 120 ms on the owner's PC; CI machines are slower
