"""DARBIT_NO_REAL_INPUT=1 (on for these tests, conftest.py): every real input, app control and screen grab raises
naming the call, read-only calls still work, and FakeGame's fakes are used instead."""

import os
import subprocess
import sys
import textwrap
from pathlib import Path

import cv2
import numpy as np
import pytest

import darbit as d
from darbit.core.geometry import Region
from darbit.platform import backend, real, screen, windows
from darbit.platform import input as device
from darbit.platform.backend import Window
from darbit.testing import FakeGame, RealInputOff

BLOCKED = [
    ("input.move", lambda: device.move(1, 2, 0)),
    ("input.move_by", lambda: device.move_by(1, 2, 0)),
    ("input.mouse_down", lambda: device.mouse_down()),
    ("input.mouse_up", lambda: device.mouse_up()),
    ("input.click", lambda: device.click(1, 2, 0)),
    ("input.drag", lambda: device.drag(1, 2, 3, 4, 0)),
    ("input.scroll", lambda: device.scroll(1)),
    ("input.key_down", lambda: device.key_down("a")),
    ("input.key_up", lambda: device.key_up("a")),
    ("input.tap", lambda: device.tap("a")),
    ("input.write", lambda: device.write("hi")),
    ("input.key_now", lambda: device.key_now("a", False)),
    ("input.button_now", lambda: device.button_now("left", False)),
    ("input.nudge", lambda: device.nudge(1, 2)),
    ("input.place", lambda: device.place(1, 2)),
    ("input.wheel_now", lambda: device.wheel_now(1)),
    ("input.let_go_of_everything", lambda: device.let_go_of_everything()),
    ("screen.grab", lambda: screen.grab()),
    ("windows.bring_to_front", lambda: windows.bring_to_front(7)),
    ("windows.close", lambda: windows.close("Game")),
    ("windows.launch", lambda: windows.launch("game.exe")),
]

GAME = Window(handle=7, title="Game", exe="game.exe", pid=70)


class Recorder:
    """A system piece that writes down every call it gets instead of touching the PC."""

    def __init__(self, calls: list[str], answers: dict[str, object]) -> None:
        self._calls = calls
        self._answers = answers

    def __getattr__(self, name: str):
        def call(*args: object, **kwargs: object) -> object:
            self._calls.append(name)
            return self._answers.get(name)

        return call


@pytest.fixture
def pieces(monkeypatch):
    """Every piece is a Recorder: what reaches the system is written down, nothing is sent."""
    calls = []
    answers = {
        "position": (5, 6),
        "desktop": (0, 0, 800, 600),
        "monitors": [Region(0, 0, 800, 600)],
        "scale_at": 1.0,
        "grab": (np.zeros((2, 2, 3), np.uint8), Region(0, 0, 2, 2)),
        "windows": [GAME],
        "matching": [GAME],
        "in_front": True,
        "region": Region(0, 0, 800, 600),
        "bring_to_front": True,
        "close": True,
    }
    for piece in ("input", "screen", "windows"):
        monkeypatch.setattr(backend, piece, lambda: Recorder(calls, answers))
    monkeypatch.setattr(d.settings, "log", False)
    return calls


def test_the_switch_is_on_for_these_tests():
    assert os.environ[real.SWITCH] == "1" and real.off()
    assert RealInputOff is real.RealInputOff  # what a bot's tests catch


@pytest.mark.parametrize(("name", "call"), BLOCKED, ids=[name for name, _ in BLOCKED])
def test_every_real_input_raises_naming_the_call(pieces, name, call):
    with pytest.raises(real.RealInputOff, match=rf"^{name}: real input is off"):
        call()
    assert pieces == []


@pytest.mark.parametrize(("name", "call"), BLOCKED, ids=[name for name, _ in BLOCKED])
def test_with_the_switch_off_the_same_calls_reach_the_system(pieces, real_input, name, call):
    call()
    assert pieces[-1] == name.split(".")[1]


@pytest.mark.parametrize("value", ["", "0"])
def test_empty_or_zero_leaves_real_input_on(monkeypatch, value):
    monkeypatch.setenv(real.SWITCH, value)
    assert not real.off()
    real.refuse("input.click")


def test_read_only_calls_still_work(pieces):
    assert device.position() == (5, 6)
    assert device.desktop() == (0, 0, 800, 600)
    assert screen.monitors() == [Region(0, 0, 800, 600)] and screen.scale_at(1, 1) == 1.0
    assert windows.windows() == [GAME] and windows.matching("Game") == [GAME]
    assert windows.in_front(7) and windows.region(7) == Region(0, 0, 800, 600)
    assert d.App("Game").running and d.App("Game").window is not None
    device.release_all()  # only lets go of what darbit held: nothing, with real input off


def test_darbits_own_calls_raise_before_anything_is_sent(pieces, monkeypatch, tmp_path):
    cv2.imwrite(str(tmp_path / "Play.png"), np.full((8, 8, 3), 200, np.uint8))
    monkeypatch.setattr(d.settings, "images", [tmp_path])
    with pytest.raises(real.RealInputOff, match="input.click"):
        d.click(d.Location(10, 20))
    with pytest.raises(real.RealInputOff, match="input.tap"):
        d.press("a")
    with pytest.raises(real.RealInputOff, match="screen.grab"):  # not "not found": the test hears why
        d.exists("Play", timeout=0)
    with pytest.raises(real.RealInputOff, match="windows.launch"):
        d.App("game.exe").open()
    with pytest.raises(real.RealInputOff, match="windows.close"):
        d.App("Game").close()
    with pytest.raises(real.RealInputOff, match="windows.bring_to_front"):
        d.App("Game").focus()
    assert "click" not in pieces and "tap" not in pieces and "grab" not in pieces


def test_fake_game_still_works_with_real_input_off(pieces, monkeypatch, tmp_path):
    menu = np.full((200, 300, 3), (40, 40, 40), np.uint8)
    menu[50:90, 60:160] = np.random.default_rng(3).integers(0, 255, (40, 100, 3), dtype=np.uint8)
    cv2.imwrite(str(tmp_path / "Menu.Bag.png"), menu[50:90, 60:160])
    bag = np.full((200, 300, 3), (10, 90, 10), np.uint8)
    monkeypatch.setattr(d.settings, "images", [tmp_path])
    monkeypatch.setattr(d.settings, "timeout", 0.3)
    monkeypatch.setattr(d.settings, "window", "Game")  # FakeGame stands in for its window too
    with FakeGame({"Menu": menu, "Bag": bag}, start="Menu") as game:
        game.leads("Menu", "Menu.Bag", "Bag").leads("Bag", "esc", "Menu", key=True)
        assert d.click("Menu.Bag") and game.showing == "Bag"
        d.press("esc")
        assert game.showing == "Menu" and game.keys == ["esc"]
        assert d.hover(d.Location(1, 1))
    assert "click" not in pieces and "tap" not in pieces and "grab" not in pieces
    with pytest.raises(real.RealInputOff):  # and once it's gone, real input is off again
        d.click(d.Location(10, 20))


def test_fake_game_answers_the_window_lookup_itself(monkeypatch, tmp_path):
    def no_system():
        raise AssertionError("the system's windows were asked")

    monkeypatch.setattr(backend, "windows", no_system)
    monkeypatch.setattr(d.settings, "log", False)
    monkeypatch.setattr(d.settings, "window", "Game")
    menu = np.full((200, 300, 3), (40, 40, 40), np.uint8)
    real_matching = windows.matching
    with FakeGame({"Menu": menu}, start="Menu") as game:
        found = windows.matching("Game")
        assert [window.title for window in found] == ["Game"]
        assert windows.in_front(found[0].handle)
        assert windows.region(found[0].handle) == Region(0, 0, 0, 0)  # window-space targets stay where taken
        assert windows.matching("gam", loose=True) == found and windows.matching("gam") == []
        assert windows.matching("Other") == []
        assert d.click(d.Location(10, 20)) and game.clicks == [(10, 20)]
    assert windows.matching is real_matching


def run_bot_tests(folder, conftest: str) -> subprocess.CompletedProcess:
    """Run pytest on a bot's tests in their own process, with the switch not set to start with."""
    (folder / "conftest.py").write_text(conftest, encoding="utf-8")
    (folder / "test_bot.py").write_text(
        textwrap.dedent(
            """
            import os

            import darbit as d
            from darbit.platform.real import RealInputOff


            def test_switch():
                assert os.environ.get("DARBIT_NO_REAL_INPUT") == "1"
                try:
                    d.press("a")
                except RealInputOff as error:
                    assert "input.tap" in str(error)
                else:
                    raise AssertionError("a key went to the PC")


            def test_back_on_for_one_test(real_input):
                assert "DARBIT_NO_REAL_INPUT" not in os.environ
            """
        ),
        encoding="utf-8",
    )
    environment = dict(os.environ)
    environment.pop(real.SWITCH)
    source = str(Path(d.__file__).parents[1])  # this darbit, wherever the tests run from
    environment["PYTHONPATH"] = os.pathsep.join([source, environment.get("PYTHONPATH", "")])
    return subprocess.run(
        [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", str(folder)],
        check=False,
        cwd=folder,
        env=environment,
        capture_output=True,
        text=True,
        timeout=120,
    )


def test_one_line_in_a_bots_conftest_turns_it_on(tmp_path):
    done = run_bot_tests(tmp_path, 'pytest_plugins = ["darbit.testing.no_real_input"]\n')
    assert done.returncode == 0, done.stdout + done.stderr
    assert "2 passed" in done.stdout


def test_without_the_line_a_bots_tests_have_it_off(tmp_path):
    done = run_bot_tests(tmp_path, "")
    assert done.returncode != 0
    assert "test_switch" in done.stdout and "real_input' not found" in done.stdout
