"""The web capture session on a fake screen: freeze, boxes around a click, Test with look-alikes, and Save."""

import json

import cv2
import numpy as np
import pytest

from darbit.capture import service
from darbit.capture.common import Item
from darbit.core.geometry import Region
from darbit.platform import screen


def fake_screen() -> np.ndarray:
    """A dark screen with two green buttons, the left one a little duller, and a grey panel."""
    shot = np.full((600, 900, 3), 30, np.uint8)
    cv2.rectangle(shot, (100, 380), (300, 440), (60, 120, 220), -1)  # a panel
    cv2.rectangle(shot, (500, 400), (650, 450), (110, 220, 90), -1)
    cv2.putText(shot, "EQUIP", (530, 435), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
    cv2.rectangle(shot, (500, 200), (650, 250), (100, 205, 85), -1)
    cv2.putText(shot, "EQUlP", (530, 235), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (240, 240, 240), 2)
    return shot


@pytest.fixture
def frozen(tmp_path, monkeypatch):
    shot = fake_screen()
    origin = Region(1920, 0, 900, 600)  # a second screen, to check offsets

    def monitors():
        return [origin]

    def grab(area=None):
        return shot.copy(), origin

    monkeypatch.setattr(screen, "monitors", monitors)
    monkeypatch.setattr(screen, "grab", grab)

    def scale_at(x, y):
        return 1.0

    monkeypatch.setattr(screen, "scale_at", scale_at)
    images = tmp_path / "assets" / "images"
    images.mkdir(parents=True)
    started = service.start(tmp_path, images, [Item("Bag.Equip", "image", "the green button", "Bag")])
    assert started["items"] == [{"name": "Bag.Equip", "kind": "image", "say": "the green button", "screen": "Bag"}]
    service.freeze()
    yield images
    service.stop()


def test_a_click_offers_boxes_around_it(frozen):
    found = service.candidates(560, 420, "image")
    boxes = found["boxes"]
    assert boxes[-1] == [0, 0, 900, 600]  # the whole screen comes last
    chosen = boxes[found["start"]]
    x, y, w, h = chosen
    assert x <= 560 <= x + w and y <= 420 <= y + h


def test_test_finds_the_button_and_its_look_alike(frozen):
    result = service.test([500, 400, 151, 51], None, None, 0.9)
    scores = []
    for match in result["matches"]:
        scores.append(match["score"])
    assert result["matches"][0]["x"] == 500  # pixels of the shot, as the overlay draws them
    assert scores[0] > 0.99
    assert len(scores) >= 2  # the duller button shows as a look-alike
    assert scores[1] < 0.99


def test_test_only_searches_the_region(frozen):
    result = service.test([500, 400, 151, 51], None, [450, 350, 300, 150], 0.9)
    assert len(result["matches"]) == 1
    assert result["searched"] == [450, 350, 300, 150]


def test_save_writes_the_target_and_moves_on(frozen):
    saved = service.save("Bag.Equip", "image", [500, 400, 150, 50], [450, 350, 300, 150], [600, 425])
    assert saved["items"] == []
    assert (frozen / "Bag.Equip.png").is_file()
    settings = json.loads((frozen / "Bag.Equip.json").read_text(encoding="utf-8"))
    assert settings["region"] == [1920 + 450, 350, 300, 150]
    assert settings["offset"] == [600 - 575, 425 - 425]


def test_points_and_regions_save_without_a_picture(frozen):
    service.save("Bag.Slot", "point", None, None, [10, 20])
    service.save("Bag.Menu", "region", [100, 100, 300, 200], None, None)
    assert json.loads((frozen / "Bag.Slot.json").read_text(encoding="utf-8"))["location"] == [1930, 20]
    assert json.loads((frozen / "Bag.Menu.json").read_text(encoding="utf-8"))["region"] == [2020, 100, 300, 200]
    assert not (frozen / "Bag.Slot.png").exists()


def test_mistakes_say_what_is_wrong(frozen):
    with pytest.raises(service.CaptureError, match="name"):
        service.save("", "image", [1, 1, 5, 5], None, None)
    with pytest.raises(service.CaptureError, match="box the image"):
        service.save("X", "image", None, None, None)
    with pytest.raises(service.CaptureError, match="click the location"):
        service.save("X", "point", None, None, None)
    with pytest.raises(service.CaptureError, match="box something"):
        service.test(None, None, None, 0.8)


def test_nothing_works_without_a_session():
    service.stop()
    with pytest.raises(service.CaptureError, match="no capture session"):
        service.freeze()


def test_the_guide_gives_the_items_in_order(tmp_path):
    (tmp_path / "guide.toml").write_text(
        'title = "Setup"\n\n[[screen]]\nname = "Bag"\nsay = "Open the bag"\n\n[[screen.take]]\nimage = "Bag.Equip"\n\n'
        '[[screen.take]]\nlocation = "Bag.Slot"\nsay = "the first slot"\n',
        encoding="utf-8",
    )
    items = service.items_for(tmp_path, "guide", "", "image")
    assert [(item.name, item.kind, item.note, item.screen) for item in items] == [
        ("Bag.Equip", "image", "Open the bag", "Bag"),
        ("Bag.Slot", "location", "the first slot", "Bag"),
    ]
    assert service.items_for(tmp_path, "one", "Lobby.Play", "point")[0].kind == "location"
    assert service.items_for(tmp_path, "new", "", "image") == []


def test_hotkeys_read_like_the_keymap():
    from darbit.platform.win32.hotkeys import MOD_ALT, MOD_CONTROL, MOD_NOREPEAT, MOD_SHIFT, parse

    assert parse("ctrl+alt+c") == (MOD_NOREPEAT | MOD_CONTROL | MOD_ALT, ord("C"))
    assert parse("Shift+F1")[0] == MOD_NOREPEAT | MOD_SHIFT
    with pytest.raises(ValueError):
        parse("ctrl+alt")
    with pytest.raises(ValueError):
        parse("a+b")


def test_saving_keeps_the_screen_with_its_assets(frozen, tmp_path):
    from darbit.project.manifest import load
    from darbit.server import library

    service.save("Bag.Equip", "image", [500, 400, 150, 50], None, None)
    service.save("Bag.Slot", "point", None, None, [100, 120])
    screens = service.screens_folder(tmp_path)
    assert (screens / "Bag.jpg").is_file()
    places = json.loads((screens / "Bag.json").read_text(encoding="utf-8"))
    assert places["w"] == 900
    assert places["assets"]["Bag.Equip"] == {"kind": "image", "box": [500, 400, 150, 50]}
    assert places["assets"]["Bag.Slot"]["kind"] == "location"
    (tmp_path / "darbit.toml").write_text(
        '[bot]\nname = "test-bot"\n[images]\nfolders = ["assets/images"]\n', encoding="utf-8"
    )
    listed = library.screens(load(tmp_path))
    assert listed[0]["screen"] == "Bag"
    assert listed[0]["picture"].startswith("data:image/jpeg;base64,")
    assert set(listed[0]["assets"]) == {"Bag.Equip", "Bag.Slot"}


def test_a_saved_picture_is_tested_in_its_own_region(frozen):
    service.save("Bag.Equip", "image", [500, 400, 150, 50], [450, 350, 300, 150], None)
    result = service.test(None, "Bag.Equip", None, 0.9)
    assert result["searched"] == [450, 350, 300, 150]  # its saved region, back in the shot's pixels
    assert len(result["matches"]) == 1


def test_images_share_a_region_by_name(frozen):
    from darbit.core.targets import load

    service.save("Bag.List", "region", None, [450, 150, 300, 350], None)  # a region of its own
    service.save("Bag.Other", "image", [100, 380, 200, 60], [90, 370, 220, 80], None)  # an image with its own region
    found = service.regions()
    assert found[0] == {"name": "Bag.List", "region": [450, 150, 300, 350], "used_by": []}  # shot pixels
    assert found[1]["name"] == "" and found[1]["used_by"] == ["Bag.Other"]
    service.save("Bag.Equip", "image", [500, 400, 150, 50], [450, 150, 300, 350], None, region_name="Bag.List")
    saved = json.loads((frozen / "Bag.Equip.json").read_text(encoding="utf-8"))
    assert saved["region"] == "Bag.List"  # by name: moving Bag.List moves it too
    assert service.regions()[0]["used_by"] == ["Bag.Equip"]
    assert service.existing("Bag.Equip")["region_name"] == "Bag.List"
    target = load("Bag.Equip", [frozen])
    assert (target.region.x, target.region.w) == (1920 + 450, 300)  # the shared region's box, on the desktop
