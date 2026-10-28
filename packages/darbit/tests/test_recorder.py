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


def move(t: float, dx: int, dy: int = 0) -> RawEvent:
    return RawEvent(t, "move", "", 0, 0, dx, dy)


def mouse_steps(events):
    found = []
    for kind, args in steps_of(events):
        if kind == "mouse":
            found.append(args)
    return found


def test_mouse_movement_is_kept_as_the_mouse_s_own_counts():
    events = []
    for tick in range(30):  # 0.3 s of moving right: a free cursor, or a camera with shift lock, it's the same
        events.append(move(tick * 0.01, 4))
    moves = mouse_steps(events)
    assert moves[0] == {"verb": "move_by", "by": [40, 0], "seconds": 0.09}
    total = 0
    for args in moves:
        total += args["by"][0]
    assert total == 120  # every count is kept


def test_movement_before_a_click_ends_before_it():
    events = [move(0.0, 5), move(0.01, 5), RawEvent(0.02, "mouse_down", "left", 50, 50)]
    events += [RawEvent(0.05, "mouse_up", "left", 50, 50)]
    assert mouse_steps(events) == [
        {"verb": "move_by", "by": [10, 0], "seconds": 0.01},
        {"verb": "click", "target": [50, 50]},
    ]


def test_turning_the_camera_with_the_right_button_plays_back_with_it_held():
    events = [RawEvent(0.0, "mouse_down", "right", 960, 540)]
    for tick in range(1, 6):
        events.append(move(tick * 0.01, 10))  # Roblox holds the cursor while the right button turns the camera
    events.append(RawEvent(0.1, "mouse_up", "right", 960, 540))
    verbs = []
    for args in mouse_steps(events):
        verbs.append(args["verb"])
    assert verbs == ["mouse_down", "move_by", "mouse_up"]
    assert mouse_steps(events)[-1] == {"verb": "mouse_up", "target": None, "button": "right"}  # let go in place


def test_a_click_with_a_little_jitter_is_still_a_click():
    events = [RawEvent(0.0, "mouse_down", "left", 50, 50), move(0.01, 2), RawEvent(0.05, "mouse_up", "left", 50, 50)]
    assert mouse_steps(events)[0] == {"verb": "click", "target": [50, 50]}


def test_wheel_notches_close_together_are_one_scroll():
    events = [
        RawEvent(0.0, "wheel", "", 10, 10, 1),
        RawEvent(0.05, "wheel", "", 10, 10, 1),
        RawEvent(0.1, "wheel", "", 10, 10, 1),
        RawEvent(1.0, "wheel", "", 10, 10, -2),
    ]
    assert mouse_steps(events) == [{"verb": "scroll", "notches": 3}, {"verb": "scroll", "notches": -2}]
