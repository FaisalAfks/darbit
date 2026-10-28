"""A recording session with fake hooks: keys and clicks become an action file; hotkeys and the bar are left out."""

import pytest

from darbit import paths
from darbit.platform import hooks
from darbit.runs import flowfile
from darbit.runtime import tape
from darbit.server import record_api

SECOND = 1_000_000_000  # ns


@pytest.fixture
def recording(tmp_path, monkeypatch):
    def project_dir(folder):
        return folder / ".darbit"

    def fake_start(on_event, moves=False):
        def stop():
            return None

        return stop

    monkeypatch.setattr(paths, "project_dir", project_dir)
    monkeypatch.setattr(hooks, "start", fake_start)
    monkeypatch.setattr(record_api, "ignore_area", None)
    monkeypatch.setattr(record_api, "on_end", None)
    (tmp_path / "darbit.toml").write_text('[bot]\nname = "test-bot"\n', encoding="utf-8")
    record_api.start(tmp_path, "dodge")
    session = record_api._recording
    session.started = 0.0
    yield tmp_path
    if record_api._recording is not None:
        record_api.stop(False)


def event(kind, code=0, x=0, y=0, at=0.0):
    record_api._on_event(kind, code, x, y, int(at * SECOND))


def test_keys_clicks_and_the_mouse_become_a_tape(recording):
    event("key_down", 0x51, at=1.0)  # q
    event("key_up", 0x51, at=1.05)
    event("mouse_move", 0, 800, 440, at=1.2)
    event("mouse_delta", 1, 12, 0, at=1.2)
    event("mouse_down", 0, 812, 440, at=1.5)
    event("mouse_up", 0, 812, 440, at=1.55)
    event("wheel", -2, 812, 440, at=1.7)
    status = record_api.status()
    assert status["count"] == 5  # press, wait, click, wait, scroll: what the bar shows
    saved = record_api.stop(True)
    assert saved == {"saved": True, "name": "dodge", "steps": 1}
    flow = flowfile.read(recording / "actions" / "dodge.py")
    assert flow.timed
    assert flow.sections[0].name == "Dodge"
    assert [(step.kind, step.args) for step in flow.sections[0].steps] == [("tape", {"start": 0, "end": 1.75})]
    saved_tape = tape.load(recording / "actions" / "dodge.tape.json")
    kinds = []
    for one in saved_tape.events:
        kinds.append((one.kind, one.name, one.up))
    assert kinds == [
        ("key", "q", False),
        ("key", "q", True),
        ("move", "", False),
        ("button", "left", False),
        ("button", "left", True),
        ("wheel", "", False),
    ]
    assert saved_tape.events[2].dx == 12
    assert saved_tape.events[5].dx == -2


def test_darbit_hotkeys_are_left_out(recording):
    event("key_down", 0xA2, at=1.0)  # ctrl
    event("key_down", 0xA4, at=1.01)  # alt
    event("key_down", 0x50, at=1.02)  # p: ctrl+alt+p, pause
    event("key_up", 0x50, at=1.05)
    event("key_up", 0xA4, at=1.06)
    event("key_up", 0xA2, at=1.07)
    event("key_down", 0x45, at=2.0)  # e
    event("key_up", 0x45, at=2.05)
    steps = record_api._recording.recorder.steps()
    assert [(step.kind, step.args) for step in steps] == [("key", {"verb": "press", "keys": ["e"]})]


def test_clicks_on_the_bar_are_left_out(recording, monkeypatch):
    def bar():
        return (600, 0, 620, 76)

    monkeypatch.setattr(record_api, "ignore_area", bar)
    event("mouse_down", 0, 700, 30, at=1.0)
    event("mouse_up", 0, 700, 30, at=1.05)
    assert record_api.status()["count"] == 0


def test_checks_while_paused_and_undo(recording):
    event("key_down", 0x51, at=1.0)
    event("key_up", 0x51, at=1.05)
    record_api.pause()
    record_api.add_check({"kind": "picture", "target": "Dim.Boss.Bar", "timeout": 20})
    record_api.pause()
    status = record_api.status()
    assert status["checks"] == 1
    assert status["steps"][-1]["text"] == 'd.wait("Dim.Boss.Bar", timeout=20)'
    record_api.remove_last()
    assert record_api.status()["checks"] == 0
    record_api.remove_last()
    assert record_api.status()["count"] == 0
    with pytest.raises(ValueError):
        record_api.add_check({"kind": "picture"})


def test_a_cancelled_recording_writes_nothing(recording):
    event("key_down", 0x51, at=1.0)
    event("key_up", 0x51, at=1.05)
    assert record_api.stop(False) == {"saved": False}
    assert not (recording / "actions" / "dodge.py").exists()
    with pytest.raises(ValueError):
        record_api.pause()
