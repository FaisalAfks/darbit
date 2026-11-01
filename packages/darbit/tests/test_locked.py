"""A locked screen: the bot lets go of everything and waits at its next darbit call, then goes on when it's back."""

import json
import threading

import pytest

from darbit import events
from darbit.errors import Stopped
from darbit.platform import safety, system
from darbit.settings import settings


@pytest.fixture
def locked(monkeypatch, tmp_path):
    """The screen locked for the next `answers` looks; the run report in a temporary folder."""
    answers = []
    monkeypatch.setattr(system, "screen_usable", lambda: answers.pop(0) if answers else True)
    monkeypatch.setattr(safety, "SCREEN_EVERY", 0.01)
    monkeypatch.setattr(safety, "_screen_looked", 0.0)
    monkeypatch.setattr(safety, "_armed", True)
    monkeypatch.setattr(safety, "_on_stop", [])
    monkeypatch.setattr(settings, "logs", tmp_path)
    monkeypatch.setattr(settings, "log", True)
    yield answers
    safety.reset()


def test_the_bot_waits_while_the_screen_is_locked(locked, tmp_path):
    seen = []
    stop_listening = events.listen(lambda topic, data: seen.append(data) if topic == "screen.locked" else None)
    let_go = []
    safety.on_stop(lambda: let_go.append(True))
    locked.extend([False, False, False, True])
    try:
        safety.check()
    finally:
        stop_listening()
    assert seen == [{"locked": True}, {"locked": False}]
    assert let_go  # held keys and buttons were let go of
    report = next(tmp_path.glob("report-*.jsonl")).read_text(encoding="utf-8").splitlines()
    assert [json.loads(line)["state"] for line in report] == ["locked", "back"]


def test_an_unlocked_screen_is_looked_at_once_a_second(locked, monkeypatch):
    looks = []
    monkeypatch.setattr(system, "screen_usable", lambda: looks.append(True) or True)
    monkeypatch.setattr(safety, "SCREEN_EVERY", 1.0)
    for _ in range(100):
        safety.check()
    assert len(looks) == 1


def test_a_stop_ends_the_wait(locked):
    locked.extend([False] * 1000)
    threading.Timer(0.1, safety.stop).start()
    with pytest.raises(Stopped, match="screen was locked"):
        safety.check()
