"""Movable pills (#384, #449): where a dropped pill goes, the work area it sits in, the edges it can use, its kept
place, and its hiding per edge."""

from pathlib import Path

import pytest

pytest.importorskip("PySide6.QtCore", exc_type=ImportError)

from darbit.platform.system import HiddenTaskbar
from darbit.studio import docking
from darbit.studio.docking import FLOATING, GAP, PULL, Held, Place, Rect
from darbit.studio.hiding import HIDE_AFTER, Peek, to_pixels

SCREEN = Rect(0, 0, 1600, 900)
ALL = ["top", "bottom", "left", "right"]


SIZES = {"row": (400.0, 56.0), "column": (150.0, 200.0), "card": (420.0, 200.0)}
TASKBAR = Rect(0, 0, 1600, 900, work=Rect(0, 0, 1600, 852))  # a 48-point taskbar along the bottom


def held(x, y, grab_x=0.5, grab_y=0.5):
    return Held(x, y, grab_x, grab_y, SIZES)


def landed(screen, place, width, height):
    """Where a dropped pill of this size sits: its top-left corner."""
    area = docking.work_of(screen)
    if place.floating:
        box = docking.floating_spot(area, place.x, place.y, width, height)
    else:
        box = docking.spot(area, place.edge, place.along, width, height)
    return box.x, box.y


def test_a_pill_dropped_by_an_edge_stays_where_it_was_let_go_along_it():
    # held by its left quarter at x 500: its left side is at 400, and that is where it sits on the top edge
    top = docking.drop(Place("main"), "main", SCREEN, ALL, held(500, 30, 0.25))
    assert top.edge == "top" and landed(SCREEN, top, 400, 56) == pytest.approx((400, GAP))
    # by the left edge as a column, held in its middle at y 300: its top is at 200
    left = docking.drop(Place("main"), "main", SCREEN, ALL, held(40, 300))
    assert left.edge == "left" and landed(SCREEN, left, 150, 200) == pytest.approx((GAP, 200))
    # dragged past a corner, it stops flush in it, never off the screen
    past = docking.drop(Place("main"), "main", SCREEN, ALL, held(1500, 20))
    assert past.along == 1.0 and landed(SCREEN, past, 400, 56) == (1600 - GAP - 400, GAP)
    # control: the same pill held anywhere else lands somewhere else; nothing moves it to fixed places
    alongs = {docking.drop(Place("main"), "main", SCREEN, ALL, held(x, 30)).along for x in (430, 470, 530, 990)}
    assert len(alongs) == 4


def test_a_drop_very_close_to_a_corner_or_the_centre_is_pulled_onto_it():
    # the centre on the top edge: the pill's left side at 600
    near = docking.drop(Place("main"), "main", SCREEN, ALL, held(800 + PULL - 2, 30))
    assert near.along == 0.5 and landed(SCREEN, near, 400, 56) == (600, GAP)
    corner = docking.drop(Place("main"), "main", SCREEN, ALL, held(GAP + 200 + PULL - 2, 30))
    assert corner.along == 0.0
    # control: a little further away it stays where it was let go
    far = docking.drop(Place("main"), "main", SCREEN, ALL, held(800 + PULL + 4, 30))
    assert far.along != 0.5 and landed(SCREEN, far, 400, 56) == pytest.approx((600 + PULL + 4, GAP))
    assert docking.pull(0.3, 1000) == 0.3 and docking.pull(0.49, 1000) == 0.5 and docking.pull(0.03, 0) == 0.0


def test_a_pill_dropped_firmly_inside_floats_exactly_where_it_was_let_go():
    inside = docking.drop(Place("main"), "main", SCREEN, ALL, held(700, 400, 0.1, 0.2))
    assert inside.edge == FLOATING
    assert landed(SCREEN, inside, 420, 200) == pytest.approx((700 - 42, 400 - 40))
    just_short = docking.float_line(SCREEN) - 1
    assert docking.drop(Place("main"), "main", SCREEN, ALL, held(800, just_short)).edge == "top"
    # floating keeps the edge it came from, for Dock
    left = docking.drop(Place("main"), "main", SCREEN, ALL, held(40, 300))
    assert docking.docked(docking.drop(left, "main", SCREEN, ALL, held(800, 450))).edge == "left"
    # control: let go half off the screen, the card is kept wholly on it
    edge = docking.floating_spot(SCREEN, 0.99, 0.99, 400, 200)
    assert edge.right <= SCREEN.right - GAP and edge.bottom <= SCREEN.bottom - GAP


def test_a_docked_pill_sits_flush_in_its_corners():
    assert docking.spot(SCREEN, "top", 0.5, 400, 56) == Rect(600, GAP, 400, 56)
    assert docking.spot(SCREEN, "right", 1.0, 150, 200) == Rect(1600 - GAP - 150, 900 - GAP - 200, 150, 200)
    assert docking.spot(SCREEN, "left", 0.0, 150, 200) == Rect(GAP, GAP, 150, 200)
    # along_of is spot the other way round
    box = docking.spot(SCREEN, "bottom", 0.37, 400, 56)
    assert docking.along_of(SCREEN, "bottom", box.x, box.y, 400, 56) == pytest.approx(0.37)


def test_pills_sit_above_the_taskbar_on_any_side():
    bottom = docking.drop(Place("main"), "main", TASKBAR, ALL, held(800, 880))
    assert bottom.edge == "bottom" and landed(TASKBAR, bottom, 400, 56) == (600, 852 - GAP - 56)
    on_right = Rect(0, 0, 1600, 900, work=Rect(0, 0, 1540, 900))
    right = docking.drop(Place("main"), "main", on_right, ALL, held(1530, 400))
    assert right.edge == "right" and landed(on_right, right, 150, 200)[0] == 1540 - GAP - 150
    on_top = Rect(0, 0, 1600, 900, work=Rect(0, 60, 1600, 840))
    assert landed(on_top, Place("main"), 400, 56) == (600, 60 + GAP)
    # a floating card let go over the taskbar is kept above it
    card = docking.floating_spot(docking.work_of(TASKBAR), 0.5, 0.99, 420, 200)
    assert card.bottom <= 852 - GAP
    # the edge is found from the work area: just above the taskbar is right by the bottom edge
    assert docking.nearest_edge(docking.work_of(TASKBAR), 800, 845, ALL) == "bottom"
    # control: a screen without a taskbar uses all of it
    assert landed(SCREEN, bottom, 400, 56) == (600, 900 - GAP - 56)


def test_a_taskbar_that_hides_itself_still_gets_its_room():
    # Windows leaves an auto-hidden taskbar out of the work area; at 150% a 72-pixel bar is 48 points
    scaled = Rect(0, 0, 1707, 1067, 1.5)
    assert docking.less_taskbars(scaled, scaled, [HiddenTaskbar("bottom", 72)]) == Rect(0, 0, 1707, 1019)
    assert docking.less_taskbars(SCREEN, SCREEN, [HiddenTaskbar("left", 60)]) == Rect(60, 0, 1540, 900)
    # control: an edge the work area already stops short of (a taskbar that stays) is not cut twice, and without a
    # hidden bar the work area is left as it is
    work = Rect(0, 0, 1600, 852)
    assert docking.less_taskbars(SCREEN, work, [HiddenTaskbar("bottom", 48)]) == work
    assert docking.less_taskbars(SCREEN, work, []) == work


def test_a_kept_place_stays_inside_the_work_area_when_the_taskbar_or_screen_changes(tmp_path, monkeypatch):
    from darbit import paths
    from darbit.studio.docking import PillPlace

    monkeypatch.setattr(paths, "config_dir", lambda: tmp_path)
    screens = {"main": SCREEN}
    place = PillPlace("run", screens=lambda: screens)
    place.setSize("row", 400, 56)
    place.begin(800, 30)
    place.move(1500, 880)  # the bottom right corner, no taskbar yet
    place.end()
    assert place.spotFor(400, 56) == {"x": 1600 - GAP - 400, "y": 900 - GAP - 56}
    screens["main"] = TASKBAR  # a taskbar comes up along the bottom
    place._screens_changed()
    assert place.spotFor(400, 56) == {"x": 1600 - GAP - 400, "y": 852 - GAP - 56}
    screens["main"] = Rect(0, 0, 1280, 720, work=Rect(0, 0, 1280, 680))  # a smaller screen
    place._screens_changed()
    assert place.spotFor(400, 56) == {"x": 1280 - GAP - 400, "y": 680 - GAP - 56}
    # floating, it is kept wholly inside the work area too
    place.begin(1100, 650)
    place.move(1000, 450)
    place.end()
    assert place.floating
    screens["main"] = Rect(0, 0, 1280, 720, work=Rect(0, 0, 1280, 400))
    place._screens_changed()
    spot = place.spotFor(420, 200)
    assert spot["y"] + 200 <= 400 - GAP and spot["x"] + 420 <= 1280 - GAP
    assert place.work == {"x": 0, "y": 0, "width": 1280, "height": 400}
    assert place.screen == {"x": 0, "y": 0, "width": 1280, "height": 720}  # tucking away goes past all of it


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
    assert docking.drop(Place("main"), "main", SCREEN, edges, held(1590, 450)).edge != "right"


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
    # a place along an edge is kept as it was left, not moved to a fixed one; one past the ends is brought in
    assert docking.read({**saved, "along": 0.62}, screens, "main").along == 0.62
    assert docking.read({**saved, "along": 3.0, "docked_along": -1}, screens, "main").along == 1.0
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
    place.setSize("column", 150, 200)
    place.holdAt(0.5, 0.25)
    place.begin(800, 30)
    place.move(30, 600)  # by the left edge: already a column, its corners and centre shown, where it lands marked
    assert place.dragging and place.form == "column" and place.near == "left"
    assert [spot["on"] for spot in place.snaps] == [False, False, False]
    assert place.landing == pytest.approx({"x": GAP + 75, "y": 650})  # held a quarter down: its middle 50 lower
    place.move(30, 400 + 10)  # very close to the centre: pulled onto it
    assert [spot["on"] for spot in place.snaps] == [False, True, False]
    assert place.landing == {"x": GAP + 75, "y": 450}
    place.move(30, 600)
    place.end()
    assert (place.edge, place.form) == ("left", "column")
    assert place.spotFor(150, 200) == pytest.approx({"x": GAP, "y": 550})
    again = PillPlace("run", screens=lambda: screens)
    assert again.edge == "left" and again.spotFor(150, 200) == pytest.approx({"x": GAP, "y": 550})
    other = PillPlace("recorder", screens=lambda: screens)
    assert other.edge == "top"  # each pill keeps its own
    again.begin(30, 600)
    again.move(800, 450)
    assert again.landing == {}  # nothing marked on the edge while it would float
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
    for name in ("RunPill", "ScoutPill", "RecorderPill"):
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
