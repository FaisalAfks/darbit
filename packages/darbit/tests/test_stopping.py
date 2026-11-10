"""A stop says what stopped the bot, and ends it with one line and exit code 0: a stop isn't a crash."""

import importlib
import os
import re
import subprocess
import sys
import time
import types
from pathlib import Path

import pytest

from darbit.errors import Stopped
from darbit.platform import backend, safety
from darbit.platform.backend import NotSupported

SRC = str(Path(__file__).resolve().parents[1] / "src")


@pytest.fixture(autouse=True)
def fresh(monkeypatch):
    monkeypatch.setattr(safety, "arm", lambda: None)  # no hotkey thread in a test
    safety.reset()
    yield
    safety.reset()


@pytest.mark.parametrize("by", [safety.HOTKEY, safety.FROM_DARBIT])
def test_a_stop_says_what_stopped_it(by):
    safety.stop(by)
    with pytest.raises(Stopped, match=re.escape(f"stopped by {by}")):
        safety.check()


def test_stop_in_darbit_comes_through_the_control_folder(tmp_path):
    (tmp_path / "stop").write_text("", encoding="utf-8")
    safety._look_at_control(tmp_path)
    with pytest.raises(Stopped, match="Stop in darbit"):
        safety.check()


class _Threads:
    """Stands in for threading.Thread: counts the threads started."""

    def __init__(self) -> None:
        self.started: list[str] = []

    def __call__(self, target, args: tuple, name: str, daemon: bool) -> "_Threads":
        self.started.append(name)
        return self

    def start(self) -> None:
        return None


@pytest.fixture
def unwatched(monkeypatch):
    """safety as if nothing had watched the stop hotkey yet, and no control folder."""
    monkeypatch.setattr(safety, "_watching", None)
    monkeypatch.setattr(safety, "_watch_keys", [()])
    monkeypatch.delenv(safety.CONTROL, raising=False)


def test_with_real_input_off_the_stop_hotkey_starts_no_thread(unwatched, monkeypatch):
    threads = _Threads()
    monkeypatch.setattr(safety.threading, "Thread", threads)
    safety.watch("ctrl+alt+q")
    assert threads.started == []


def test_with_real_input_off_only_the_control_folder_is_watched(unwatched, monkeypatch, tmp_path):
    threads = _Threads()
    monkeypatch.setattr(safety.threading, "Thread", threads)
    monkeypatch.setenv(safety.CONTROL, str(tmp_path))
    safety.watch("ctrl+alt+q")
    assert threads.started == ["darbit-control"]


class _Keyboard:
    """A system's System piece that only answers keys_down, counting the calls."""

    def __init__(self) -> None:
        self.looks = 0
        self.done = False

    def keys_down(self, codes: tuple[int, ...]) -> bool:
        if self.done:
            raise NotSupported("the test is over")  # the thread stops reading keys
        self.looks += 1
        return False


def _system_piece(monkeypatch, platform: str, piece: object) -> None:
    """Make `platform`'s System piece this system's, but with `piece`'s keys_down; its other pieces stay this
    system's too, for whatever else runs meanwhile."""
    name = f"stopping_test_system_{platform}"
    module = types.ModuleType(name)
    module.__dict__.update(vars(importlib.import_module(backend.MODULES[sys.platform]["system"])))
    module.keys_down = piece.keys_down
    monkeypatch.setitem(sys.modules, name, module)
    monkeypatch.setitem(backend.MODULES, platform, {**backend.MODULES[sys.platform], "system": name})


def _wait_for_looks(keyboard: _Keyboard, looks: int) -> None:
    deadline = time.monotonic() + 5
    while keyboard.looks < looks and time.monotonic() < deadline:
        time.sleep(0.01)
    assert keyboard.looks >= looks


def test_the_stop_hotkey_keeps_the_system_it_started_on(unwatched, real_input, monkeypatch):
    """A test that pretends to run on another system (sys.platform) doesn't send the watching thread there."""
    here = _Keyboard()
    elsewhere = _Keyboard()
    other = "win32" if sys.platform != "win32" else "linux"
    _system_piece(monkeypatch, other, elsewhere)
    _system_piece(monkeypatch, sys.platform, here)
    try:
        safety.watch("ctrl+alt+q")
        _wait_for_looks(here, 1)
        with monkeypatch.context() as pretend:
            pretend.setattr(sys, "platform", other)
            started = here.looks
            _wait_for_looks(here, started + 3)
        assert elsewhere.looks == 0
    finally:
        here.done = True


def _run(code: str) -> subprocess.CompletedProcess:
    env = {**os.environ, "PYTHONPATH": SRC}
    return subprocess.run(
        [sys.executable, "-c", code], check=False, capture_output=True, text=True, env=env, timeout=60
    )


def test_a_stopped_bot_ends_quietly_with_code_0():
    ended = _run("import darbit\nfrom darbit.errors import Stopped\nraise Stopped('stopped by the stop hotkey')")
    assert ended.returncode == 0
    assert "Traceback" not in ended.stderr and "darbit: stopped by the stop hotkey" in ended.stderr


def test_a_real_error_still_shows_its_traceback():
    ended = _run("import darbit\nraise KeyError('a bug')")
    assert ended.returncode == 1 and "Traceback" in ended.stderr and "KeyError" in ended.stderr
