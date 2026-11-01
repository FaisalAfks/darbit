"""The screen map: where the game is, the way between screens, and getting there, on saved screens (FakeGame)."""

import cv2
import numpy as np
import pytest

import darbit as d
from darbit.testing import FakeGame


def button(image, x, y, colour, text):
    cv2.rectangle(image, (x, y), (x + 160, y + 60), colour, -1)
    cv2.putText(image, text, (x + 14, y + 40), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 255, 255), 2)
    return image[y : y + 60, x : x + 160].copy()


@pytest.fixture
def game(tmp_path, monkeypatch):
    """Four made-up screens (Lobby, Bag, Shop, an ad) and their buttons as the bot's pictures."""
    monkeypatch.setattr(d.settings, "images", [tmp_path])
    monkeypatch.setattr(d.settings, "log", False)
    monkeypatch.setattr(d.settings, "timeout", 0.3)
    monkeypatch.setattr(d.settings, "scan_rate", 50)
    monkeypatch.setattr(d.settings, "similarity", 0.9)
    screens = {}
    pictures = {}
    for name, colour in (("Lobby", (60, 40, 30)), ("Bag", (30, 60, 40)), ("Shop", (40, 30, 70)), ("Ad", (20, 20, 20))):
        screens[name] = np.full((500, 800, 3), colour, np.uint8)
    pictures["Lobby.Title"] = button(screens["Lobby"], 20, 20, (200, 120, 40), "LOBBY")
    pictures["Lobby.Bag"] = button(screens["Lobby"], 300, 400, (40, 160, 60), "BAG")
    pictures["Lobby.Shop"] = button(screens["Lobby"], 520, 400, (160, 60, 160), "SHOP")
    pictures["Bag.Title"] = button(screens["Bag"], 20, 20, (60, 200, 90), "BAG")
    pictures["Bag.Back"] = button(screens["Bag"], 20, 400, (90, 90, 90), "BACK")
    pictures["Shop.Title"] = button(screens["Shop"], 20, 20, (180, 70, 200), "SHOP")
    pictures["Ad.Close"] = button(screens["Ad"], 600, 20, (30, 30, 200), "CLOSE")
    for name, pixels in pictures.items():
        cv2.imwrite(str(tmp_path / f"{name}.png"), pixels)
    return screens


@pytest.fixture
def world():
    game_map = d.Map()
    game_map.screen("Lobby", "Lobby.Title").screen("Bag", "Bag.Title").screen("Shop", "Shop.Title")
    game_map.screen("Ad", "Ad.Close")
    game_map.move("Lobby", "Bag", "Lobby.Bag").move("Bag", "Lobby", "Bag.Back")
    game_map.move("Lobby", "Shop", "Lobby.Shop").move("Shop", "Lobby", lambda: d.press("esc"))
    game_map.move("Ad", "Lobby", "Ad.Close")
    return game_map


def test_the_map_knows_where_the_game_is_and_the_way(game, world):
    with FakeGame(game, start="Bag") as fake:
        assert world.where() == "Bag"
        fake.showing = "Shop"
        assert world.where() == "Shop"
    assert [(move.start, move.end) for move in world.route("Bag", "Shop")] == [("Bag", "Lobby"), ("Lobby", "Shop")]
    assert world.route("Lobby", "Lobby") == []
    assert world.route("Ad", "Ad") == [] and world.route("Lobby", "Ad") is None


def test_go_walks_there_by_clicks_and_keys(game, world):
    with FakeGame(game, start="Bag") as fake:
        fake.leads("Bag", "Bag.Back", "Lobby").leads("Lobby", "Lobby.Shop", "Shop").leads(
            "Shop", "esc", "Lobby", key=True
        )
        assert world.go("Shop")
        assert fake.showing == "Shop"
        fake.leads("Lobby", "Lobby.Bag", "Bag")
        assert world.go("Bag")  # Shop -> Lobby by Esc, then the Bag button
        assert fake.showing == "Bag" and fake.keys == ["esc"]


def test_go_takes_a_new_way_when_a_move_lands_somewhere_else(game, world):
    with FakeGame(game, start="Lobby") as fake:
        fake.leads("Lobby", "Lobby.Bag", "Ad", once=True)  # an ad pops up the first time
        fake.leads("Lobby", "Lobby.Bag", "Bag").leads("Ad", "Ad.Close", "Lobby")
        assert world.go("Bag")
        assert fake.showing == "Bag"
        assert len(fake.clicks) == 3  # Bag (the ad), Close, Bag


def test_go_says_when_it_is_lost_or_has_no_way(game, world):
    unknown = np.zeros((500, 800, 3), np.uint8)
    with FakeGame({**game, "Nowhere": unknown}, start="Nowhere"):
        assert world.go("Bag") is False
    with FakeGame(game, start="Lobby"):
        assert world.go("Ad") is False  # nothing leads to the ad
    with pytest.raises(ValueError, match="no screen called"):
        world.go("Moon")
    with pytest.raises(ValueError, match="no screen called"):
        world.move("Lobby", "Moon", "Lobby.Bag")
