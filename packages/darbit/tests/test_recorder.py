"""Recording: fake keyboard and mouse events into steps (presses, combos, holds, clicks, waits)."""

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
    assert steps_of(events) == [("key", {"verb": "press", "keys": ["shift+e"]})]  # one press, not two


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
    assert found[2].args == {"verb": "mouse_down", "target": [100, 100], "button": "right"}  # a drag
    assert found[4].args == {"verb": "mouse_up", "target": [300, 100], "button": "right"}


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


def turn(t: float, dx: int, x: int = 960, y: int = 540) -> RawEvent:
    return RawEvent(t, "turn", "", x, y, dx, 0)


def test_mouse_movement_while_the_game_holds_the_cursor_is_a_camera_turn():
    events = []
    for tick in range(30):  # 0.3 s of moving right, the cursor held in the middle (shift lock)
        events.append(turn(tick * 0.01, 4))
    steps = steps_of(events)
    assert steps[0] == ("mouse", {"verb": "move_by", "by": [80, 0], "seconds": 0.19})
    assert steps[-1][1]["verb"] == "move_by"
    total = 0
    for kind, args in steps:
        if kind == "mouse":
            total += args["by"][0]
    assert total == 120  # every count is kept


def test_moving_the_cursor_around_isnt_a_turn():
    events = []
    for tick in range(10):
        events.append(turn(tick * 0.01, 10, x=100 + tick * 12))  # the cursor follows the mouse
    assert steps_of(events) == []


def test_a_right_drag_is_a_turn_even_when_the_cursor_moves():
    events = [RawEvent(0.0, "mouse_down", "right", 100, 100)]
    for tick in range(1, 6):
        events.append(turn(tick * 0.01, 10, x=100 + tick * 10))
    events.append(RawEvent(0.1, "mouse_up", "right", 150, 100))
    found = steps_of(events)
    assert ("mouse", {"verb": "move_by", "by": [50, 0], "seconds": 0.04}) in found


def test_turning_the_camera_with_the_right_button_plays_back_with_it_held():
    events = [RawEvent(0.0, "mouse_down", "right", 960, 540)]
    for tick in range(1, 6):
        events.append(turn(tick * 0.01, 10))  # Roblox holds the cursor while the right button turns the camera
    events.append(RawEvent(0.1, "mouse_up", "right", 960, 540))
    verbs = []
    for kind, args in steps_of(events):
        if kind == "mouse":
            verbs.append(args["verb"])
    assert verbs == ["mouse_down", "move_by", "mouse_up"]
    assert steps_of(events)[-1] == ("mouse", {"verb": "mouse_up", "target": None, "button": "right"})  # in place
