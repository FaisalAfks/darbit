"""settings.front: the bot's window brought forward before input, and with "always" before searches too."""

from types import SimpleNamespace

import numpy as np
import pytest

import darbit as d
from darbit.core.geometry import Region
from darbit.project import manifest
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


def test_by_default_the_window_comes_forward_before_input_only(game):
    front.before_search()
    assert game.brought == 0
    front.before_input()
    assert game.brought == 1


def test_always_brings_it_forward_before_a_search(game, monkeypatch):
    monkeypatch.setattr(d.settings, "front", "always")
    front.before_search()
    assert game.brought == 1
    front.before_search()  # already in front: left alone
    assert game.brought == 1


def test_no_window_set_or_none_open_is_left_alone(game, monkeypatch):
    monkeypatch.setattr(d.settings, "front", "always")
    monkeypatch.setattr(d.settings, "window", None)
    front.before_search()
    monkeypatch.setattr(d.settings, "window", "Elsewhere")
    front.before_input()
    assert game.brought == 0


def test_every_search_asks_first(game, monkeypatch, tmp_path):
    from darbit.core.targets import save
    from darbit.platform import screen

    save(tmp_path / "Play", np.full((8, 8, 3), 200, np.uint8))
    monkeypatch.setattr(d.settings, "images", [tmp_path])
    monkeypatch.setattr(d.settings, "log", False)
    monkeypatch.setattr(d.settings, "front", "always")
    monkeypatch.setattr(screen, "grab", lambda area=None: (np.zeros((40, 40, 3), np.uint8), Region(0, 0, 40, 40)))
    assert d.exists("Play") is None
    assert game.brought == 1


@pytest.mark.parametrize("value", ["input", "always", "opened"])
def test_darbit_toml_takes_front(value):
    manifest._check_setting("front", value)


def test_darbit_toml_refuses_another_front():
    with pytest.raises(manifest.ProjectError, match='front is "input", "always" or "opened"'):
        manifest._check_setting("front", "sometimes")


@pytest.fixture
def opened(game, monkeypatch):
    monkeypatch.setattr(d.settings, "front", "opened")
    monkeypatch.setattr(front, "_seen", set())
    return game


def test_opened_brings_a_new_window_forward_once(opened):
    front.before_search()
    assert opened.brought == 1
    opened.ahead = False  # the owner switched to another window
    front.before_search()
    front.before_input()
    assert opened.brought == 1


def test_opened_brings_a_reopened_window_forward_again(opened, monkeypatch):
    front.before_search()
    opened.ahead = False
    monkeypatch.setattr(opened, "matching", lambda name, loose=False: [SimpleNamespace(handle=8)])
    front.before_input()
    assert opened.brought == 2
