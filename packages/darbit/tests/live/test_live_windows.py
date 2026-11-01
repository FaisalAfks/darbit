"""darbit on a real Windows desktop: screen capture, the mouse, the keyboard, window lookup, tapes, the listener,
the input worker and the Studio's windows, all on target.py's window. See conftest.py for when these run."""

import os
import time
from pathlib import Path

import pytest
from target import PICTURE, PICTURE_AT, TITLE

import darbit as d
from darbit.platform import hooks
from darbit.runtime import tape

SHOTS = Path(os.environ.get("DARBIT_LIVE_SHOTS", "live-shots"))


def picture_box(target) -> tuple[int, int, int, int]:
    client = target.client
    return (client["x"] + PICTURE_AT[0], client["y"] + PICTURE_AT[1], 64, 48)


def front(target) -> None:
    assert d.App(TITLE).focus(), "the target window didn't come to the front"
    target.settle(0.3)


def test_the_window_is_found_where_it_is(target):
    found = d.App(TITLE).window
    client = target.client
    assert found is not None
    assert (found.x, found.y, found.w, found.h) == (client["x"], client["y"], client["w"], client["h"])


def test_a_picture_is_found_on_the_real_screen(target):
    front(target)
    match = d.find(PICTURE)
    assert match is not None, "the picture wasn't found on screen"
    assert (match.x, match.y, match.w, match.h) == picture_box(target)
    assert match.score > 0.99


def test_a_click_lands_on_the_picture(target):
    front(target)
    before = len(target.events("click"))
    assert d.click(PICTURE)
    target.settle()
    clicks = target.events("click")[before:]
    assert len(clicks) == 1
    x, y, w, h = picture_box(target)
    assert clicks[0]["button"] == "LeftButton"
    assert abs(clicks[0]["x"] - (x + w // 2)) <= 1 and abs(clicks[0]["y"] - (y + h // 2)) <= 1


def test_keys_and_text_reach_the_window(target):
    front(target)
    before = len(target.events("key"))
    d.press("a", "b")
    d.write("Hi 5")
    target.settle()
    typed = "".join(event["text"] for event in target.events("key")[before:])
    assert typed == "abHi 5"


def test_window_space_finds_the_picture_in_the_window(target, darbit_settings, monkeypatch):
    front(target)
    monkeypatch.setattr(darbit_settings, "space", "window")
    monkeypatch.setattr(darbit_settings, "window", TITLE)
    match = d.find(PICTURE)
    assert match is not None
    assert (match.x, match.y) == picture_box(target)[:2]


def test_a_tape_plays_every_event_on_time(target, tmp_path):
    """Keys and a click from a tape reach the window at the gaps they were recorded at."""
    front(target)
    x, y, w, h = picture_box(target)
    spot = (x + w // 2, y + h // 2)
    events = [
        tape.Event(0.10, "key", "a"),
        tape.Event(0.18, "key", "a", up=True),
        tape.Event(0.50, "key", "b"),
        tape.Event(0.62, "key", "b", up=True),
        tape.Event(0.80, "move", x=spot[0], y=spot[1]),
        tape.Event(0.90, "button", "left", x=spot[0], y=spot[1]),
        tape.Event(0.95, "button", "left", up=True, x=spot[0], y=spot[1]),
        tape.Event(1.40, "key", "c"),
        tape.Event(1.45, "key", "c", up=True),
    ]
    action = tmp_path / "timing.py"
    tape.save(tape.path_for(action), tape.Tape(events))
    start = len(target.events())
    tape.replay(action)
    target.settle(0.5)
    got = [event for event in target.events()[start:] if event["kind"] in ("key", "key_up", "click", "release")]
    assert [event["kind"] for event in got] == ["key", "key_up", "key", "key_up", "click", "release", "key", "key_up"]
    wanted = [0.10, 0.18, 0.50, 0.62, 0.90, 0.95, 1.40, 1.45]
    errors = [(event["t"] - got[0]["t"]) - (at - wanted[0]) for event, at in zip(got, wanted, strict=True)]
    print("tape timing, ms off per event:", [round(error * 1000, 1) for error in errors])
    assert max(abs(error) for error in errors) < 0.010, "an event went more than 10 ms off its time"
    assert abs(got[4]["x"] - spot[0]) <= 1 and abs(got[4]["y"] - spot[1]) <= 1


def test_the_listener_leaves_darbits_own_input_out(target):
    """What darbit sends isn't the person: the recorder never records it."""
    front(target)
    heard = []
    stop = hooks.start(lambda *event: heard.append(event), moves=True)
    try:
        time.sleep(0.3)
        d.press("x")
        d.click(PICTURE)
        time.sleep(0.5)
    finally:
        stop()
    assert heard == []


def test_the_input_worker_runs_a_recording(tmp_path):
    from darbit.project import bots
    from darbit.studio.worker_link import WorkerLink

    folder = bots.new("live-bot", tmp_path)
    link = WorkerLink(lambda topic, data: None)
    try:
        started = link.call("record.start", path=str(folder), name="nothing_much")
        assert started
        time.sleep(0.5)
        assert link.call("record.status")["recording"] is True
        assert link.call("record.stop", keep=False) == {"saved": False}
    finally:
        link.close()


@pytest.mark.parametrize("page", ["overview", "library", "results", "settings", "studio"])
def test_the_studio_draws_on_windows(page, tmp_path):
    """The Studio's pages drawn by Qt on Windows, kept as pictures (the CI keeps them)."""
    from darbit.studio import app

    SHOTS.mkdir(parents=True, exist_ok=True)
    path = SHOTS / f"studio-{page}.png"
    app.shot(path, page)
    assert path.is_file() and path.stat().st_size > 10_000


def test_highlight_finds_the_picture_and_lets_clicks_through(target, pictures, tmp_path):
    """Highlight on the real screen: it boxes the picture where it is, and its overlay doesn't take the clicks."""
    import shutil

    from PySide6.QtCore import QCoreApplication
    from PySide6.QtGui import QGuiApplication
    from PySide6.QtQuick import QQuickWindow

    from darbit.platform import input as device
    from darbit.platform import screen
    from darbit.project import bots
    from darbit.service.client import Client
    from darbit.studio.app import load
    from darbit.studio.backend import Studio
    from darbit.studio.highlight import Highlight

    folder = bots.new("highlight-bot", tmp_path)
    shutil.copy(pictures / f"{PICTURE}.png", folder / "assets" / "images" / f"{PICTURE}.png")
    front(target)
    app = QGuiApplication.instance() or QGuiApplication(["live"])
    studio = Studio(lambda: Client("live"), "glass-dark", "")
    highlight = Highlight()
    engine = load(studio, highlight=highlight)
    root = engine.rootObjects()[0]  # held, or Qt deletes it under findChild
    overlay = root.findChild(QQuickWindow, "highlightWindow")
    root.hide()
    highlight.start(folder)

    def spin(seconds: float) -> None:
        deadline = time.monotonic() + seconds
        while time.monotonic() < deadline:
            QCoreApplication.processEvents()
            time.sleep(0.01)

    try:
        deadline = time.monotonic() + 10
        while highlight.found < 1 and time.monotonic() < deadline:
            spin(0.1)
        boxes = [box for box in highlight.boxes if box["name"] == PICTURE]
        assert boxes and boxes[0]["found"], f"Highlight didn't find the picture: {highlight.boxes}"
        assert (boxes[0]["x"], boxes[0]["y"], boxes[0]["w"], boxes[0]["h"]) == picture_box(target)
        assert overlay.isVisible()
        spin(0.5)
        SHOTS.mkdir(parents=True, exist_ok=True)
        pixels, _ = screen.grab()
        import cv2

        scale = os.environ.get("QT_SCALE_FACTOR", "1")
        cv2.imwrite(str(SHOTS / f"highlight-on-windows-{scale}.png"), pixels)
        x, y, w, h = picture_box(target)
        left_of_it = pixels[y + h // 2, x - 8 : x].astype(int)  # the box's border is drawn just outside the picture
        assert any(g > 150 and g > r + 40 for b, g, r in left_of_it), "Highlight's box isn't around the picture"
        before = len(target.events("click"))
        x, y, w, h = picture_box(target)
        device.click(x + w // 2, y + h // 2, 0.0)
        spin(0.4)
        assert len(target.events("click")) == before + 1, "the click stopped at Highlight's overlay"
    finally:
        highlight.stop()
        spin(0.2)
        del engine
        app.processEvents()


def test_capture_takes_the_picture_pixel_for_pixel(target, pictures, tmp_path):
    """The capture tool on the real screen: a click on the picture boxes it, and what it saves is the picture."""
    import cv2
    import numpy as np
    from PySide6.QtCore import QCoreApplication
    from PySide6.QtGui import QGuiApplication

    from darbit.platform import screen
    from darbit.project import bots
    from darbit.service.client import Client
    from darbit.studio.app import load
    from darbit.studio.backend import Studio
    from darbit.studio.capture import Capture, ShotProvider

    folder = bots.new("capture-bot", tmp_path)
    front(target)
    app = QGuiApplication.instance() or QGuiApplication(["live"])
    provider = ShotProvider()
    capture = Capture(provider)
    engine = load(Studio(lambda: Client("live"), "glass-dark", ""), capture=capture)
    root = engine.rootObjects()[0]  # held, or Qt deletes it
    root.hide()
    try:
        capture.start(folder)
        x, y, w, h = picture_box(target)
        origin = screen.desktop()
        box = [x - origin.x, y - origin.y, w, h]  # the shot starts at the desktop's top left
        found = capture.candidates(box[0] + w // 2, box[1] + h // 2, "image")
        assert box in found["boxes"], f"no candidate is the picture: {found}"
        tested = capture.test(box, None)
        assert len(tested["matches"]) == 1 and tested["matches"][0]["score"] > 0.99
        deadline = time.monotonic() + 1
        while time.monotonic() < deadline:
            QCoreApplication.processEvents()
            time.sleep(0.01)
        SHOTS.mkdir(parents=True, exist_ok=True)
        cv2.imwrite(str(SHOTS / "capture-on-windows.png"), screen.grab()[0])
        assert capture.save("Live.Patch", "image", box, None, None).get("error") is None
    finally:
        capture.close()
        QCoreApplication.processEvents()
        del engine
        app.processEvents()
    saved = next(folder.rglob("Live.Patch.png"))
    assert np.array_equal(cv2.imread(str(saved)), cv2.imread(str(pictures / f"{PICTURE}.png")))


def test_the_recorder_pill_shows_while_the_studio_is_hidden(tmp_path):
    """Recording: the worker records, and its pill shows on its own with the Studio out of the way."""
    from PySide6.QtCore import QCoreApplication
    from PySide6.QtGui import QGuiApplication
    from PySide6.QtQuick import QQuickWindow

    from darbit.project import bots
    from darbit.service.client import Client
    from darbit.studio.app import load
    from darbit.studio.backend import Studio
    from darbit.studio.recorder import Recorder

    def spin(seconds: float) -> None:
        deadline = time.monotonic() + seconds
        while time.monotonic() < deadline:
            QCoreApplication.processEvents()
            time.sleep(0.01)

    folder = bots.new("record-bot", tmp_path)
    app = QGuiApplication.instance() or QGuiApplication(["live"])
    recorder = Recorder()
    engine = load(Studio(lambda: Client("live"), "glass-dark", ""), recorder=recorder)
    root = engine.rootObjects()[0]  # held, or Qt deletes it
    pill = root.findChild(QQuickWindow, "recorderPill")
    root.hide()
    try:
        assert recorder.start(folder, "walk") == ""
        spin(1.5)
        assert recorder.active
        assert pill.isVisible(), "the recorder pill didn't show"
        SHOTS.mkdir(parents=True, exist_ok=True)
        pill.grabWindow().save(str(SHOTS / "recorder-pill-on-windows.png"))
    finally:
        recorder.finish(False)
        recorder.close()
        spin(0.3)
        del engine
        app.processEvents()


def test_the_ghost_cursor_shows_the_bots_click_and_key(target):
    """darbit's clicks and keys reach the Studio's ghost cursor, and the click still reaches the window under it."""
    from PySide6.QtCore import QCoreApplication
    from PySide6.QtGui import QGuiApplication
    from PySide6.QtQuick import QQuickWindow

    from darbit.platform import ghost as told
    from darbit.service.client import Client
    from darbit.studio.app import load
    from darbit.studio.backend import Studio
    from darbit.studio.ghost import Ghost

    def spin(seconds: float) -> None:
        deadline = time.monotonic() + seconds
        while time.monotonic() < deadline:
            QCoreApplication.processEvents()
            time.sleep(0.01)

    app = QGuiApplication.instance() or QGuiApplication(["live"])
    ghost = Ghost()
    engine = load(Studio(lambda: Client("live"), "glass-dark", ""), ghost=ghost)
    root = engine.rootObjects()[0]  # held, or Qt deletes it
    overlay = root.findChild(QQuickWindow, "ghostWindow")
    root.hide()
    ghost.start()
    told.forget()
    try:
        front(target)
        before = len(target.events("click"))
        assert d.click(PICTURE)
        d.press("q")
        spin(0.2)
        kinds = [(mark["kind"], mark["name"]) for mark in ghost.marks]
        assert ("click", "left") in kinds and ("key", "q") in kinds, kinds
        click = next(mark for mark in ghost.marks if mark["kind"] == "click")
        x, y, w, h = picture_box(target)
        assert (click["x"], click["y"]) == (x + w // 2, y + h // 2)
        assert overlay.isVisible()
        target.settle()
        assert len(target.events("click")) == before + 1, "the click stopped at the ghost cursor"
    finally:
        ghost.stop()
        spin(0.2)
        del engine
        app.processEvents()
