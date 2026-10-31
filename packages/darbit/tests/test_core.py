import cv2
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


def smooth_screen(size=(400, 600)) -> np.ndarray:
    """A screen with soft shapes, so resized copies of a part of it still look alike."""
    rng = np.random.default_rng(4)
    noise = rng.integers(0, 255, (size[0] // 8, size[1] // 8, 3), dtype=np.uint8)
    return cv2.resize(noise, (size[1], size[0]), interpolation=cv2.INTER_CUBIC)


def test_options_from_settings():
    assert matching.Options.from_dict({}) is matching.PLAIN
    options = matching.Options.from_dict({"fast": True, "sizes": True})
    assert options.fast and options.sizes == matching.DEFAULT_SIZES
    assert matching.Options.from_dict({"sizes": [0.5]}).sizes == (0.5,)


def test_grayscale_and_fast_find_the_same_spot():
    screen = smooth_screen()
    target = Target(image="x", _pixels=screen[200:260, 300:400].copy())
    for options in ({"grayscale": True}, {"fast": True}, {"fast": True, "grayscale": True}):
        found = matching.best(target, screen, Region(0, 0, 600, 400), 0.9, matching.Options.from_dict(options))
        assert (found.x, found.y) == (300, 200), options


def test_fast_finds_the_target_and_not_a_look_alike_next_to_it():
    screen = smooth_screen()
    image = screen[200:260, 300:400].copy()
    look_alike = image.copy()
    look_alike[20:30, 40:50] = 255 - look_alike[20:30, 40:50]  # one small part differs
    screen[40:100, 60:160] = look_alike
    target = Target(image="x", _pixels=image)
    for options in ({"fast": True}, {"fast": True, "grayscale": True}):
        found = matching.best(target, screen, Region(0, 0, 600, 400), 0.9, matching.Options.from_dict(options))
        assert (found.x, found.y) == (300, 200), options
        assert found.score > 0.99


def test_sizes_finds_a_target_taken_at_another_size():
    screen = smooth_screen()
    bigger = cv2.resize(screen[200:260, 300:400], (125, 75), interpolation=cv2.INTER_LINEAR)  # taken at 1.25x
    target = Target(image="x", _pixels=bigger)
    whole = Region(0, 0, 600, 400)
    assert matching.best(target, screen, whole, 0.9) is None
    found = matching.best(target, screen, whole, 0.9, matching.Options.from_dict({"sizes": True}))
    assert abs(found.x - 300) <= 2 and abs(found.y - 200) <= 2 and found.w == 100


def test_closest_gives_the_best_spot_even_below_similarity():
    target = Target(image="x", _pixels=patch(seed=3))
    found = matching.closest(target, screen_with(patch(), (0, 0)), Region(0, 0, 300, 200), 0.9)
    assert found is not None and found.score < 0.9


def test_colour_tells_apart_an_icon_in_other_colours():
    screen = smooth_screen()
    image = screen[200:260, 300:400].copy()
    screen[200:260, 300:400] = 255 - image  # the image itself isn't on screen
    twin = image // 2 + np.array([0, 120, 0], np.uint8)  # the same shapes in other colours
    screen[100:160, 100:200] = twin
    target = Target(image="x", _pixels=image)
    whole = Region(0, 0, 600, 400)
    plain = matching.best(target, screen, whole, 0.8)
    assert plain is not None and (plain.x, plain.y) == (100, 100)
    assert matching.best(target, screen, whole, 0.8, matching.Options(colour=True)) is None


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
