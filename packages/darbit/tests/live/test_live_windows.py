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
