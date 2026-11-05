"""settings.window: the bot's window brought forward before input, and never before a search."""

from types import SimpleNamespace

import numpy as np
import pytest

import darbit as d
from darbit.core.geometry import Region
from darbit.runtime import front


class _Windows:
    """Stands in for the system's windows: one called Game, behind something until it's brought forward."""

    def __init__(self) -> None:
        self.ahead = False
        self.brought = 0

    def matching(self, name, loose=False):
        return [SimpleNamespace(handle=7)] if name == "Game" else []

    def in_front(self, handle):
        return self.ahead

    def bring_to_front(self, handle):
        self.brought += 1
        self.ahead = True
        return True


@pytest.fixture
def game(monkeypatch):
    windows = _Windows()
    monkeypatch.setattr(front, "windows", windows)
    monkeypatch.setattr(d.settings, "window", "Game")
    return windows


def test_the_window_comes_forward_before_input(game):
    front.before_input()
    assert game.brought == 1
    front.before_input()  # already in front: left alone
    assert game.brought == 1


def test_no_window_set_or_none_open_is_left_alone(game, monkeypatch):
    monkeypatch.setattr(d.settings, "window", None)
    front.before_input()
    monkeypatch.setattr(d.settings, "window", "Elsewhere")
    front.before_input()
    assert game.brought == 0


def test_a_search_leaves_the_windows_alone(game, monkeypatch, tmp_path):
    from darbit.core.targets import save
    from darbit.platform import screen

    save(tmp_path / "Play", np.full((8, 8, 3), 200, np.uint8))
    monkeypatch.setattr(d.settings, "images", [tmp_path])
    monkeypatch.setattr(d.settings, "log", False)
    monkeypatch.setattr(screen, "grab", lambda area=None: (np.zeros((40, 40, 3), np.uint8), Region(0, 0, 40, 40)))
    assert d.exists("Play") is None
    assert game.brought == 0
