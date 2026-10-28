"""Input tapes: telling a held cursor from a free one, saving, playing on time with a fake mouse and keyboard."""

import time

import pytest

from darbit.errors import Stopped
from darbit.platform import input as device
from darbit.platform import safety
from darbit.runtime import tape
from darbit.runtime.tape import Event, Tape


def moves(start: float, count: int, step_x: int, cursor_step: int, shown: bool = True) -> list[Event]:
    found = []
    for index in range(count):
        found.append(Event(start + index * 0.002, "move", dx=step_x, x=500 + index * cursor_step, y=300, shown=shown))
    return found


def test_a_cursor_the_game_puts_back_is_held_and_a_free_one_isnt():
    free = moves(0.0, 30, 3, 4)  # the cursor follows the mouse
    held = moves(0.1, 30, 3, 0)  # the mouse moves, the cursor stays (shift lock)
    hidden = moves(0.2, 30, 3, 9, shown=False)  # hidden while the game holds it (a right-drag)
    events = free + held + hidden
    tape.mark_held(events)
    assert not free[-1].held
    assert held[-1].held
    assert hidden[0].held


def test_a_game_putting_the_cursor_back_each_frame_holds_it():
    events = []
    for index in range(40):  # the cursor follows for a few packets, then the game puts it back in the middle
        events.append(Event(index * 0.002, "move", dx=4, x=960 + (index % 8) * 4, y=540))
    tape.mark_held(events)
    assert events[-1].held


def test_a_cursor_pushed_against_the_screen_edge_is_free():
    pushed = []
    for index in range(30):
        pushed.append(Event(index * 0.002, "move", dx=5, x=1919, y=300))
    tape.mark_held(pushed, [0, 0, 1920, 1080])
    assert not pushed[-1].held


def test_a_tape_saves_and_loads(tmp_path):
    saved = Tape([Event(0.5, "key", "w"), Event(0.6, "move", dx=-3, dy=2, x=10, y=20, held=True)], [0, 0, 800, 600])
    path = tape.path_for(tmp_path / "run.py")
    assert path.name == "run.tape.json"
    tape.save(path, saved)
    assert tape.load(path) == Tape(saved.events, [0, 0, 800, 600], None)


@pytest.fixture
def sent(monkeypatch):
    found = []

    def key_now(name, up):
        found.append(("key", name, up))
        times.append(time.perf_counter())

    def button_now(button, up):
        found.append(("button", button, up))

    def nudge(dx, dy):
        found.append(("nudge", dx, dy))

    def place(x, y):
        found.append(("place", x, y))

    def wheel_now(notches, sideways=False):
        found.append(("wheel", notches, sideways))

    def nothing():
        return None

    times = []
    monkeypatch.setattr(device, "key_now", key_now)
    monkeypatch.setattr(device, "button_now", button_now)
    monkeypatch.setattr(device, "nudge", nudge)
    monkeypatch.setattr(device, "place", place)
    monkeypatch.setattr(device, "wheel_now", wheel_now)
    monkeypatch.setattr(safety, "check", nothing)
    monkeypatch.setattr(tape.actions, "_front", nothing)
    monkeypatch.setattr(tape, "_window_now", nothing)
    tape.stopping.clear()
    return found, times


def test_a_tape_plays_every_event_on_time(tmp_path, sent):
    found, times = sent
    events = [
        Event(0.0, "move", dx=4, x=100, y=100),
        Event(0.01, "move", dx=4, x=100, y=100),  # same place: not sent again
        Event(0.02, "button", "left", x=120, y=100),  # the cursor goes there first
        Event(0.05, "button", "left", True, x=120, y=100),
        Event(0.10, "move", dx=7, dy=-2, x=960, y=540, held=True),  # held: the counts go as they came
        Event(0.12, "key", "w"),
        Event(0.30, "key", "w", True),
        Event(0.31, "wheel", dx=-1),
    ]
    tape.save(tape.path_for(tmp_path / "run.py"), Tape(events))
    began = time.perf_counter()
    tape.replay(tmp_path / "run.py", 0.0, 0.35)
    took = time.perf_counter() - began
    assert found == [
        ("place", 100, 100),
        ("place", 120, 100),
        ("button", "left", False),
        ("button", "left", True),
        ("nudge", 7, -2),
        ("key", "w", False),
        ("key", "w", True),
        ("wheel", -1, False),
    ]
    assert times[1] - times[0] == pytest.approx(0.18, abs=0.003)  # the key was held as long as it was
    assert took == pytest.approx(0.35, abs=0.03)  # it waits out the part's end


def test_a_part_of_a_tape_plays_from_its_start(tmp_path, sent):
    found, times = sent
    events = [Event(0.1, "key", "a"), Event(1.0, "key", "b"), Event(1.05, "key", "b", True)]
    tape.save(tape.path_for(tmp_path / "run.py"), Tape(events))
    tape.replay(tmp_path / "run.py", 1.0)
    assert found == [("key", "b", False), ("key", "b", True)]
    assert times[1] - times[0] == pytest.approx(0.05, abs=0.003)


def test_places_follow_the_game_window():
    place = tape.Placing([100, 100, 800, 600], [300, 50, 1600, 1200])
    assert place.spot(500, 400) == (300 + 800, 50 + 600)  # the middle of the window stays the middle
    assert tape.Placing(None, [0, 0, 10, 10]).spot(5, 6) == (5, 6)


def test_stop_ends_a_tape(tmp_path, sent):
    tape.save(tape.path_for(tmp_path / "run.py"), Tape([Event(5.0, "key", "a")]))
    tape.stopping.set()
    with pytest.raises(Stopped):
        tape.replay(tmp_path / "run.py")
    tape.stopping.clear()


def test_the_studio_gets_a_short_summary():
    events = moves(0.0, 600, 2, 1)
    events.append(Event(1.0, "key", "e"))
    events.append(Event(1.1, "key", "e", True))
    events.append(Event(1.5, "button", "left", x=10, y=10))
    found = tape.summary(Tape(events, screen=[0, 0, 1920, 1080]))
    assert (found["moves"], found["keys"], found["clicks"]) == (600, 1, 1)
    assert len(found["path"]) <= tape.SUMMARY_POINTS
    assert found["marks"][0] == {"t": 1.0, "kind": "key", "text": "e"}
    assert found["seconds"] == 1.5
