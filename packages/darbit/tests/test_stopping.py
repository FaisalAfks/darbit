"""A stop says what stopped the bot, and ends it with one line and exit code 0: a stop isn't a crash."""

import os
import re
import subprocess
import sys
from pathlib import Path

import pytest

from darbit.errors import Stopped
from darbit.platform import safety

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
