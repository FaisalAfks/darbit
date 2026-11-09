"""`approach`: a click with the mouse already on or near its spot steps back first, so the game sees it move in."""

import pytest

import darbit as d
from darbit.runtime import actions


class FakeMouse:
    """Where the mouse is, and every move and click, on a 1920x1080 desktop."""

    def __init__(self, x: int, y: int) -> None:
        self.at = (x, y)
        self.path: list[tuple] = []

    def position(self) -> tuple[int, int]:
        return self.at

    def desktop(self) -> tuple[int, int, int, int]:
        return (0, 0, 1920, 1080)

    def move(self, x: int, y: int, glide: float) -> None:
        self.path.append(("move", x, y, glide))
        self.at = (x, y)

    def click(self, x: int, y: int, glide: float, button: str = "left", times: int = 1) -> None:
        self.path.append(("click", x, y, glide))
        self.at = (x, y)


@pytest.fixture
def mouse(monkeypatch):
    def place(x: int, y: int) -> FakeMouse:
        fake = FakeMouse(x, y)
        for name in ("position", "desktop", "move", "click"):
            monkeypatch.setattr(actions.device, name, getattr(fake, name))
        return fake

    monkeypatch.setattr(d.settings, "log", False)
    monkeypatch.setattr(d.settings, "glide", 0.2)
    monkeypatch.setattr(d.settings, "approach", 40)
    return place


def test_already_there_steps_back_up_then_glides_in(mouse):
    fake = mouse(500, 400)
    assert d.click(d.Location(500, 400))
    assert fake.path == [("move", 500, 360, 0), ("click", 500, 400, 0.2)]


def test_near_steps_back_on_away_from_the_spot(mouse):
    fake = mouse(510, 400)
    d.click(d.Location(500, 400))
    assert fake.path == [("move", 540, 400, 0), ("click", 500, 400, 0.2)]


def test_far_just_glides_in(mouse):
    fake = mouse(100, 100)
    d.click(d.Location(500, 400))
    assert fake.path == [("click", 500, 400, 0.2)]


def test_a_retry_steps_back_again(mouse):
    fake = mouse(100, 100)
    d.click(d.Location(500, 400))
    d.click(d.Location(500, 400))  # the mouse is on it from the first click
    assert fake.path == [("click", 500, 400, 0.2), ("move", 500, 360, 0), ("click", 500, 400, 0.2)]


def test_stepping_back_stays_on_the_desktop(mouse):
    fake = mouse(10, 5)
    d.click(d.Location(10, 5))  # up is off the top: left next, also off; then right
    assert fake.path[0] == ("move", 50, 5, 0)


def test_off_by_default(mouse, monkeypatch):
    monkeypatch.setattr(d.settings, "approach", 0)
    fake = mouse(500, 400)
    d.click(d.Location(500, 400))
    assert fake.path == [("click", 500, 400, 0.2)]


def test_a_bot_sets_it_in_darbit_toml(tmp_path):
    from darbit.project.manifest import load

    (tmp_path / "darbit.toml").write_text('[bot]\nname = "a-bot"\n[settings]\napproach = 30\n', encoding="utf-8")
    assert load(tmp_path).settings["approach"] == 30
