"""What the bot sees (#316): a look kept as a small frame with its boxes, only while the Studio watches."""

import json
import os
import time

import cv2
import numpy as np
import pytest

import darbit as d
from darbit import paths
from darbit.core.geometry import Region
from darbit.core.targets import save
from darbit.platform import screen
from darbit.runtime import sees

SCREEN = Region(0, 0, 1280, 720)


@pytest.fixture
def bot(tmp_path, monkeypatch):
    """A fake screen with a button that can be shown, the bot's logs folder, and the grabs made."""
    shown = {"pixels": np.random.default_rng(1).integers(0, 255, (SCREEN.h, SCREEN.w, 3), dtype=np.uint8)}
    button = np.random.default_rng(2).integers(0, 255, (40, 60, 3), dtype=np.uint8)
    images = tmp_path / "images"
    images.mkdir()
    save(images / "Gui.Play", button)
    grabs = []

    def grab(region=None):
        area = SCREEN if region is None else region.intersect(SCREEN)
        grabs.append(area)
        return shown["pixels"][area.y : area.bottom, area.x : area.right].copy(), area

    monkeypatch.setattr(screen, "grab", grab)
    monkeypatch.setattr(screen, "monitors", lambda: [SCREEN])
    monkeypatch.setattr(screen, "desktop", lambda: SCREEN)
    monkeypatch.setattr(paths, "data_dir", lambda: tmp_path / "data")
    monkeypatch.setattr(d.settings, "images", [images])
    monkeypatch.setattr(d.settings, "logs", tmp_path / "logs")
    monkeypatch.setattr(d.settings, "log", False)
    monkeypatch.setattr(d.settings, "window", None)
    sees.forget()

    def show_button(x, y):
        shown["pixels"][y : y + 40, x : x + 60] = button

    yield {"show": show_button, "grabs": grabs, "button": button, "images": images, "logs": tmp_path / "logs"}
    sees.settled()
    sees._watched[0] = False  # the next test file starts with nobody watching


def watch(logs, age=0.0):
    """The Studio watching the bot with these logs, its file written `age` seconds ago."""
    place = sees.watching_file()
    place.parent.mkdir(parents=True, exist_ok=True)
    place.write_text(json.dumps({"logs": str(logs)}), encoding="utf-8")
    if age:
        then = time.time() - age
        os.utime(place, (then, then))
    sees.forget()


def last_look(logs):
    assert sees.settled()  # made on its own thread
    return json.loads((logs / sees.LOOK).read_text(encoding="utf-8"))


def test_nothing_is_kept_or_grabbed_while_nobody_watches(bot):
    bot["show"](300, 200)
    assert d.exists("Gui.Play.png") is not None
    assert sees.settled()
    assert len(bot["grabs"]) == 1  # the look's own grab, nothing more
    assert not (bot["logs"] / sees.LOOK).exists()


@pytest.mark.parametrize("how", ["another bot", "a Studio that went away"])
def test_a_watching_file_for_another_bot_or_gone_stale_keeps_nothing(bot, tmp_path, how):
    if how == "another bot":
        watch(tmp_path / "other" / "logs")
    else:
        watch(bot["logs"], age=sees.FRESH + 5)
    d.exists("Gui.Play.png")
    assert sees.settled()
    assert not (bot["logs"] / sees.LOOK).exists()


def test_a_found_target_is_boxed_on_a_small_frame(bot):
    watch(bot["logs"])
    bot["show"](640, 360)
    assert d.wait("Gui.Play.png", timeout=0) is not None
    look = last_look(bot["logs"])
    assert (look["kind"], look["targets"], look["found"]) == ("wait", ["Gui.Play.png"], "Gui.Play.png")
    assert (look["w"], look["h"]) == (640, 360)  # 1280 x 720 at half size
    assert look["boxes"] == [
        {"name": "Gui.Play.png", "x": 320, "y": 180, "w": 30, "h": 20, "score": 1.0, "found": True}
    ]
    frame = cv2.imread(str(bot["logs"] / look["file"]))
    assert frame.shape == (360, 640, 3)
    assert len(bot["grabs"]) == 1  # the look covered the whole screen: its own pixels were used


def test_a_target_not_found_is_boxed_at_its_closest_spot(bot):
    watch(bot["logs"])
    bot["show"](100, 100)
    half = bot["button"].copy()
    half[:, 30:] = 0  # half of it: close, but not enough
    save(bot["images"] / "Gui.Half", half)
    assert d.exists("Gui.Half.png") is None
    look = last_look(bot["logs"])
    assert look["found"] is None
    (box,) = look["boxes"]
    assert (box["x"], box["y"], box["found"]) == (50, 50, False)
    assert box["score"] < d.settings.similarity


def test_a_search_region_still_gives_a_frame_of_the_whole_screen(bot):
    save(bot["images"] / "Gui.Corner", bot["button"], region=[600, 300, 200, 200])
    bot["show"](640, 360)
    watch(bot["logs"])
    assert d.exists("Gui.Corner.png") is not None
    assert last_look(bot["logs"])["boxes"][0]["x"] == 320
    assert bot["grabs"] == [Region(600, 300, 200, 200), SCREEN]  # the look's, then once more for the frame


def test_frames_come_at_most_once_a_second_unless_what_was_found_changes(bot):
    watch(bot["logs"])
    d.exists("Gui.Play.png")
    first = last_look(bot["logs"])["time"]
    d.exists("Gui.Play.png")
    assert last_look(bot["logs"])["time"] == first  # not due yet
    bot["show"](0, 0)
    sees._last["at"] -= sees.CHANGED_EVERY
    d.exists("Gui.Play.png")
    assert last_look(bot["logs"])["found"] == "Gui.Play.png"  # found now: shown without waiting the full second


def test_a_frame_that_cant_be_written_never_stops_a_look(bot, monkeypatch):
    watch(bot["logs"])
    bot["show"](0, 0)

    def refuse(path, data):
        raise PermissionError("the Studio has it open")

    monkeypatch.setattr(sees, "_replace", refuse)
    assert d.exists("Gui.Play.png") is not None
    assert sees.settled()
    assert not (bot["logs"] / sees.LOOK).exists()


def test_a_look_while_nobody_watches_costs_next_to_nothing(bot):
    """Not a speed test of the machine: the check a look makes, a thousand times, stays far under a millisecond each."""
    started = time.perf_counter()
    for _ in range(1000):
        sees.look("exists", [], [], None, np.zeros((1, 1, 3), np.uint8), SCREEN)
    assert (time.perf_counter() - started) / 1000 < 0.0005
