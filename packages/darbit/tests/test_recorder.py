"""Recording: fake keyboard and mouse events into steps (presses, combos, holds, clicks, waits)."""

from darbit.platform import hooks
from darbit.runs.flowfile import Step
from darbit.runs.recorder import RawEvent, Recorder, key_name


def steps_of(events):
    recorder = Recorder()
    for event in events:
        recorder.add(event)
    found = []
    for step in recorder.steps():
        found.append((step.kind, step.args))
    return found


def test_taps_holds_and_waits():
    events = [
        RawEvent(1.00, "key_down", "q"),
        RawEvent(1.05, "key_up", "q"),
        RawEvent(1.50, "key_down", "w"),
        RawEvent(2.50, "key_up", "w"),
    ]
    assert steps_of(events) == [
        ("key", {"verb": "press", "keys": ["q"]}),
        ("wait", {"seconds": 0.5}),
        ("key", {"verb": "hold", "keys": ["w"]}),
        ("wait", {"seconds": 1.0}),
        ("key", {"verb": "release", "keys": ["w"]}),
    ]


def test_a_modifier_held_makes_a_combo():
    events = [
        RawEvent(0.0, "key_down", "shift"),
        RawEvent(0.05, "key_down", "e"),
        RawEvent(0.10, "key_up", "e"),
        RawEvent(0.20, "key_up", "shift"),
    ]
    assert steps_of(events) == [("key", {"verb": "press", "keys": ["shift", "e"]})]


def test_a_modifier_alone_is_its_own_press():
    assert steps_of([RawEvent(0.0, "key_down", "shift"), RawEvent(0.05, "key_up", "shift")]) == [
        ("key", {"verb": "press", "keys": ["shift"]})
    ]


def test_clicks_land_where_the_button_went_down():
    events = [
        RawEvent(0.0, "mouse_down", "left", 812, 440),
        RawEvent(0.08, "mouse_up", "left", 812, 441),
        RawEvent(0.6, "mouse_down", "right", 100, 100),
        RawEvent(0.7, "mouse_up", "right", 300, 100),
    ]
    recorder = Recorder()
    for event in events:
        recorder.add(event)
    found = recorder.steps()
    assert (found[0].kind, found[0].args) == ("mouse", {"verb": "click", "target": [812, 440]})
    assert found[1].args == {"seconds": 0.6}
    assert found[2].args == {"verb": "right_click", "target": [100, 100]}
    assert "drag" in found[2].note


def test_pausing_skips_events_and_checks_land_in_time():
    recorder = Recorder()
    recorder.add(RawEvent(0.0, "key_down", "q"))
    recorder.add(RawEvent(0.05, "key_up", "q"))
    recorder.paused = True
    recorder.add(RawEvent(0.5, "key_down", "x"))
    recorder.add(RawEvent(0.55, "key_up", "x"))
    recorder.add_step(1.0, Step("check", {"verb": "wait for", "target": "Dim.Boss.Bar", "timeout": 30}))
    recorder.paused = False
    recorder.add(RawEvent(2.0, "key_down", "e"))
    recorder.add(RawEvent(2.05, "key_up", "e"))
    kinds = []
    for step in recorder.steps():
        kinds.append(step.kind)
    assert kinds == ["key", "wait", "check", "wait", "key"]


def test_key_codes_have_keymap_names():
    assert key_name(0x45) == "e"
    assert key_name(0xA0) == "shift"
    assert key_name(0x70) == "f1"
    assert key_name(0xFF) == ""


def test_injected_keys_are_not_recorded():
    assert hooks.key_is_real(0)
    assert not hooks.key_is_real(hooks.LLKHF_INJECTED)
