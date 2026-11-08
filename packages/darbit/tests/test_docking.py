"""Movable pills (#384): where a dropped pill goes, the edges it can use, its kept place, and its hiding per edge."""

from pathlib import Path

import pytest

pytest.importorskip("PySide6.QtCore", exc_type=ImportError)

from darbit.studio import docking
from darbit.studio.docking import FLOATING, Place, Rect
from darbit.studio.hiding import HIDE_AFTER, Peek, to_pixels

SCREEN = Rect(0, 0, 1600, 900)
ALL = ["top", "bottom", "left", "right"]


def test_a_pill_dropped_near_an_edge_snaps_to_its_nearest_place_and_dropped_firmly_inside_floats():
    left = docking.drop(Place("main"), "main", SCREEN, ALL, 40, 300)
    assert (left.edge, left.along) == ("left", 0.3)  # near the centre, on the upper side
    corner = docking.drop(Place("main"), "main", SCREEN, ALL, 1590, 880)
    assert corner.edge in ("bottom", "right") and corner.along == 1.0
    top = docking.drop(Place("main"), "main", SCREEN, ALL, 790, 20)
    assert (top.edge, top.along) == ("top", 0.5)
    # control: the same pill let go well inside the float line floats where it was let go
    inside = docking.drop(Place("main"), "main", SCREEN, ALL, 800, 450)
    assert inside.edge == FLOATING and (inside.x, inside.y) == (0.5, 0.5)
    just_short = docking.float_line(SCREEN) - 1
    assert docking.drop(Place("main"), "main", SCREEN, ALL, 800, just_short).edge == "top"
    # floating keeps the edge it came from, for Dock
    assert docking.docked(docking.drop(left, "main", SCREEN, ALL, 800, 450)).edge == "left"


def test_a_docked_pill_sits_in_its_corner_or_centre_and_a_floating_one_stays_on_screen():
    assert docking.spot(SCREEN, "top", 0.5, 400, 56) == Rect(600, docking.GAP, 400, 56)
    assert docking.spot(SCREEN, "right", 1.0, 150, 200) == Rect(
        1600 - docking.GAP - 150, 900 - docking.GAP - 200, 150, 200
    )
    assert docking.spot(SCREEN, "left", 0.0, 150, 200) == Rect(docking.GAP, docking.GAP, 150, 200)
    kept_in = docking.floating_spot(SCREEN, 0.99, 0.99, 400, 200)
    assert kept_in.right <= SCREEN.right and kept_in.bottom <= SCREEN.bottom


def test_an_edge_another_screen_touches_is_left_out():
    second = Rect(1600, 0, 1280, 720)
    assert docking.free_edges(SCREEN, [second]) == ["top", "bottom", "left"]
    assert docking.free_edges(second, [SCREEN]) == ["top", "bottom", "right"]
    above = Rect(200, -1080, 1920, 1080)
    assert "top" not in docking.free_edges(SCREEN, [above])
    # control: a screen on its own, or one that only meets at a corner, keeps every edge
    assert docking.free_edges(SCREEN, []) == ALL
    assert docking.free_edges(SCREEN, [Rect(1600, 900, 800, 600)]) == ALL
    # dropped by the shared edge, it docks on the nearest edge it can use
    edges = docking.free_edges(SCREEN, [second])
    assert docking.drop(Place("main"), "main", SCREEN, edges, 1590, 450).edge != "right"


def test_screens_with_different_scaling_meet_where_their_pixels_do():
    # Qt keeps each screen's corner in pixels and scales its size: a 150% laptop 1920 pixels wide is 1280 points wide,
    # and the monitor on its right starts at 1920
    laptop = Rect(0, 0, 1280, 720, 1.5)
    monitor = Rect(1920, 0, 2560, 1440, 1.0)
    assert "right" not in docking.free_edges(laptop, [monitor])
    assert "left" not in docking.free_edges(monitor, [laptop])
    left_of = Rect(-1920, 0, 1280, 720, 1.5)  # the same laptop on the left of a 100% main screen
    assert "left" not in docking.free_edges(Rect(0, 0, 2560, 1440), [left_of])
    assert "right" not in docking.free_edges(left_of, [Rect(0, 0, 2560, 1440)])
    # control: two screens at the same scaling, and a scaled one that doesn't reach
    assert "right" not in docking.free_edges(SCREEN, [Rect(1600, 0, 1600, 900)])
    assert docking.free_edges(laptop, [Rect(2200, 0, 1600, 900)]) == ALL


def test_a_kept_place_comes_back_and_one_on_a_screen_now_gone_goes_to_the_top_centre():
    screens = {"main": SCREEN, "side": Rect(1600, 0, 1280, 720)}
    saved = {
        "screen": "side",
        "edge": "right",
        "along": 0.7,
        "x": 0.5,
        "y": 0.4,
        "docked_edge": "right",
        "docked_along": 0.7,
    }
    assert docking.read(saved, screens, "main") == Place("side", "right", 0.7, 0.5, 0.4, "right", 0.7)
    floating = {**saved, "edge": FLOATING, "x": 0.3, "y": 0.6}
    assert docking.read(floating, screens, "main").floating
    # control: the same place with its screen gone, an edge now shared, or a broken value
    assert docking.read(saved, {"main": SCREEN}, "main") == Place("main")
    assert docking.read({**saved, "screen": "main"}, screens, "main") == Place("main")
    assert docking.read({"along": "x"}, screens, "main") == Place("main")
    assert docking.read(None, screens, "main") == Place("main")


def test_a_pills_place_is_kept_in_the_ui_settings_and_read_back(tmp_path, monkeypatch):
    from darbit import paths
    from darbit.studio.docking import PillPlace

    monkeypatch.setattr(paths, "config_dir", lambda: tmp_path)
    screens = {"main": SCREEN}
    place = PillPlace("run", screens=lambda: screens)
    assert (place.edge, place.form) == ("top", "row")
    place.begin(800, 30)
    place.move(30, 600)  # by the left edge: already a column, its snap places shown
    assert place.dragging and place.form == "column" and place.near == "left"
    assert [spot["on"] for spot in place.snaps] == [False, False, False, True, False]
    place.end()
    assert (place.edge, place.form) == ("left", "column")
    again = PillPlace("run", screens=lambda: screens)
    assert (again.edge, again.shown().along) == ("left", 0.7)
    other = PillPlace("recorder", screens=lambda: screens)
    assert other.edge == "top"  # each pill keeps its own
    again.begin(30, 600)
    again.move(800, 450)
    again.end()
    assert again.floating and again.form == "card"
    again.dock()
    assert again.edge == "left" and not again.floating
    # control: a pill dragged and let go where it was is where it was
    again.begin(30, 600)
    again.cancel()
    assert again.edge == "left"


def test_a_pill_in_one_window_uses_that_window_as_its_screen(tmp_path, monkeypatch):
    from darbit import paths
    from darbit.studio.docking import PillPlace

    monkeypatch.setattr(paths, "config_dir", lambda: tmp_path)
    place = PillPlace("capture", screens=lambda: {"far": Rect(5000, 0, 100, 100)}, in_window=True)
    place.useArea(0, 0, 1000, 600)
    assert place.spotFor(200, 56) == {"x": 400.0, "y": docking.GAP}
    place.begin(500, 20)
    place.move(990, 300)
    place.end()
    assert place.edge == "right"


def test_a_pill_hides_past_its_own_edge_and_comes_back_only_there():
    # docked on the right: its area runs from the pill to the screen's right edge
    peek = Peek(left=1400, top=300, width=200, height=200, edge="right", left_at=0.0)
    peek.mouse(1500, 400, 1.0)
    peek.mouse(600, 400, 2.0)
    assert peek.time_to_tuck(2.0 + HIDE_AFTER)
    peek.tucked = True
    assert not peek.mouse(1599, 100, 9.0)  # the edge, but not beside the pill
    assert not peek.mouse(1, 400, 9.0)  # the other edge
    assert peek.mouse(1599, 400, 9.0)
    bottom = Peek(left=600, top=800, width=400, height=100, edge="bottom", tucked=True)
    assert not bottom.mouse(800, 0, 1.0) and bottom.mouse(800, 899, 1.0)
    # control: floating or being dragged it never hides
    held = Peek(left=600, top=300, width=400, height=200, edge="top", left_at=0.0, held=True)
    assert not held.time_to_tuck(100.0)
    held.held = False
    assert held.time_to_tuck(100.0)


def test_points_become_pixels_from_the_screens_own_corner():
    second = Rect(1920, 0, 1280, 720)  # 150% scaling: 1920 x 1080 pixels
    assert to_pixels(Rect(1920 + 100, 10, 200, 50), second, 1.5) == Rect(1920 + 150, 15, 300, 75)
    # control: on a screen at 100%, the points are the pixels
    assert to_pixels(Rect(100, 10, 200, 50), Rect(0, 0, 1920, 1080), 1.0) == Rect(100, 10, 200, 50)


def test_every_pill_is_the_shared_one():
    qml = Path(docking.__file__).parent / "qml"
    for name in ("RunPill", "HighlightPill", "RecorderPill"):
        source = (qml / f"{name}.qml").read_text(encoding="utf-8")
        assert "\nPillWindow {" in source, f"{name} is a PillWindow"
        assert "IconButton" not in source, f"{name}: a pill's buttons are PillActions, labelled in a column"
    capture = (qml / "CaptureWindow.qml").read_text(encoding="utf-8")
    assert "PillBody {" in capture and "PillGuide {" in capture and "captureHiding" in capture
    window = (qml / "PillWindow.qml").read_text(encoding="utf-8")
    assert "PillBody {" in window and "PillGuide {" in window
    for page in qml.glob("*.qml"):
        source = page.read_text(encoding="utf-8")
        assert "tuckTimer" not in source, f"{page.name} hides its pill its own way: use hiding.py"
