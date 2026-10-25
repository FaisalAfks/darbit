import numpy as np
import pytest

from darbit.core import matching
from darbit.core.geometry import Location, Region
from darbit.core.targets import Target, find_file, load, save
from darbit.errors import TargetError


def screen_with(patch: np.ndarray, at: tuple[int, int], size=(200, 300)) -> np.ndarray:
    rng = np.random.default_rng(1)
    screen = rng.integers(0, 255, (*size, 3), dtype=np.uint8)
    y, x = at
    screen[y : y + patch.shape[0], x : x + patch.shape[1]] = patch
    return screen


def patch(seed=2, size=(20, 30)) -> np.ndarray:
    return np.random.default_rng(seed).integers(0, 255, (*size, 3), dtype=np.uint8)


def test_region_helpers():
    r = Region(10, 20, 100, 50)
    assert r.center == Location(60, 45)
    assert r.intersect(Region(0, 0, 50, 50)) == Region(10, 20, 40, 30)
    assert r.intersect(Region(500, 500, 1, 1)) is None


def test_best_finds_the_image_in_screen_pixels():
    image = patch()
    target = Target(image="x", _pixels=image)
    found = matching.best(target, screen_with(image, (40, 70)), Region(100, 200, 300, 200), 0.9)
    assert (found.x, found.y) == (170, 240)
    assert found.score > 0.99


def test_best_returns_none_below_similarity():
    target = Target(image="x", _pixels=patch(seed=3))
    assert matching.best(target, screen_with(patch(), (0, 0)), Region(0, 0, 300, 200), 0.9) is None


def test_every_finds_each_copy_once():
    image = patch()
    screen = screen_with(image, (10, 10))
    screen[100:120, 200:230] = image
    found = matching.every(Target(image="x", _pixels=image), screen, Region(0, 0, 300, 200), 0.9)
    assert sorted((m.x, m.y) for m in found) == [(10, 10), (200, 100)]


def test_click_point_uses_offset():
    found = matching.best(
        Target(image="x", offset=(5, -5), _pixels=patch()), screen_with(patch(), (0, 0)), Region(0, 0, 300, 200), 0.9
    )
    assert found.point == Location(20, 5)


def test_dotted_names_keep_their_dots(tmp_path):
    save(tmp_path / "Gui.Play", patch(), similarity=0.9, region=[1, 2, 3, 4])
    assert (tmp_path / "Gui.Play.png").is_file()
    assert (tmp_path / "Gui.Play.json").is_file()
    assert find_file("Gui.Play", [tmp_path]) == tmp_path / "Gui.Play.png"
    target = load("Gui.Play.png", [tmp_path])
    assert target.similarity == 0.9 and target.region == Region(1, 2, 3, 4)
    assert target.pixels.shape == (20, 30, 3)


def test_location_only_target(tmp_path):
    save(tmp_path / "afk" / "spot", None, location=[10, 20])
    target = load("afk/spot", [tmp_path])
    assert target.location == Location(10, 20)


def test_missing_image_is_an_error(tmp_path):
    with pytest.raises(TargetError):
        load("nothing.png", [tmp_path])
