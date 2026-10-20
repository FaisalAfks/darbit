"""Finding and waiting against a fake screen."""
import numpy as np
import pytest

import darbit as d
from darbit.core.geometry import Region
from darbit.core.targets import save
from darbit.platform import screen


@pytest.fixture
def fake(tmp_path, monkeypatch):
    rng = np.random.default_rng(1)
    shown = {"pixels": rng.integers(0, 255, (400, 600, 3), dtype=np.uint8)}
    button = np.random.default_rng(2).integers(0, 255, (20, 30, 3), dtype=np.uint8)
    save(tmp_path / "Gui.Play", button)

    def grab(region=None):
        whole = Region(0, 0, 600, 400)
        region = whole if region is None else region.intersect(whole)
        if region is None:
            return np.zeros((0, 0, 3), np.uint8), Region(0, 0, 0, 0)
        return shown["pixels"][region.y : region.bottom, region.x : region.right].copy(), region

    monkeypatch.setattr(screen, "grab", grab)
    monkeypatch.setattr(d.settings, "images", [tmp_path])
    monkeypatch.setattr(d.settings, "log", False)

    def show_button(at):
        x, y = at
        shown["pixels"][y : y + 20, x : x + 30] = button

    return show_button


def test_exists_finds_a_shown_image(fake):
    fake((100, 50))
    found = d.exists("Gui.Play.png")
    assert (found.x, found.y) == (100, 50)
    assert found.name == "Gui.Play.png"


def test_exists_returns_none_when_not_there(fake):
    assert d.exists("Gui.Play.png") is None


def test_region_limits_the_search(fake):
    fake((100, 50))
    assert d.exists("Gui.Play.png", region=Region(300, 0, 300, 400)) is None
    assert d.exists("Gui.Play.png", region=Region(50, 0, 300, 400)) is not None


def test_wait_returns_first_of_several(fake, tmp_path):
    save(tmp_path / "Other", np.random.default_rng(9).integers(0, 255, (20, 30, 3), dtype=np.uint8))
    fake((100, 50))
    found = d.wait("Other", "Gui.Play.png", timeout=0)
    assert found.name == "Gui.Play.png"


def test_vanish(fake):
    assert d.vanish("Gui.Play.png", timeout=0)
    fake((0, 0))
    assert not d.vanish("Gui.Play.png", timeout=0)


def test_missing_images_can_be_skipped(fake, monkeypatch):
    monkeypatch.setattr(d.settings, "missing_images", "skip")
    assert d.exists("nope.png") is None
    assert d.click("nope.png", timeout=0) is False


def test_check_lists_missing_images(fake):
    assert d.check("Gui.Play.png", "nope.png") == ["nope.png"]
