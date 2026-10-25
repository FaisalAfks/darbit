import numpy as np

from darbit.core.geometry import Region
from darbit.core.targets import Target, save
from darbit.tools.check import check, check_one, main, report


def screen_with(*placed):
    shot = np.random.default_rng(1).integers(0, 255, (300, 400, 3), dtype=np.uint8)
    for image, (x, y) in placed:
        shot[y : y + image.shape[0], x : x + image.shape[1]] = image
    return shot, Region(0, 0, 400, 300)


def picture(seed):
    return np.random.default_rng(seed).integers(0, 255, (20, 30, 3), dtype=np.uint8)


def target(image, region=None):
    return Target(image="T", name="T", region=region, similarity=0.85, _pixels=image)


def test_ok_when_found_in_its_region_and_alone():
    image = picture(2)
    shot, origin = screen_with((image, (50, 50)))
    result = check_one(target(image, Region(0, 0, 150, 150)), shot, origin, "s")
    assert result.verdict == "ok" and result.at == (50, 50) and result.elsewhere < 0.5


def test_risky_when_something_else_looks_alike():
    image = picture(2)
    shot, origin = screen_with((image, (50, 50)), (image, (300, 200)))
    assert check_one(target(image, Region(0, 0, 150, 150)), shot, origin, "s").verdict == "risky"


def test_moved_when_only_found_outside_its_region():
    image = picture(2)
    shot, origin = screen_with((image, (300, 200)))
    result = check_one(target(image, Region(0, 0, 150, 150)), shot, origin, "s")
    assert result.verdict == "moved" and result.at == (300, 200)


def test_not_seen_and_best_over_several_screens():
    image = picture(2)
    blank, origin = screen_with()
    shown, _ = screen_with((image, (10, 10)))
    results = check([target(image)], [("lobby", blank, origin), ("menu", shown, origin)])
    assert results[0].verdict == "ok" and results[0].screen == "menu"
    assert check([target(image)], [("lobby", blank, origin)])[0].verdict == "not seen"
    assert "1 ok" in report(results)


def test_the_command_against_saved_screens(tmp_path, capsys):
    images, shots = tmp_path / "images", tmp_path / "shots"
    image = picture(2)
    save(images / "Gui.Play", image, region=[0, 0, 150, 150], similarity=0.85)
    shot, _ = screen_with((image, (40, 60)))
    shots.mkdir()
    import cv2

    cv2.imwrite(str(shots / "lobby.png"), shot)
    assert main(["--folder", str(images), "--screens", str(shots)]) == 0
    assert "Gui.Play.png  ok" in capsys.readouterr().out
    assert (tmp_path / ".darbit" / "state" / "check.jsonl").read_text().count("Gui.Play") == 1
