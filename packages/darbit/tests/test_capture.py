import numpy as np

from darbit.capture import distinct
from darbit.core.geometry import Region


def test_distinct_scores_low_for_a_unique_image():
    shot = np.random.default_rng(1).integers(0, 255, (200, 300, 3), dtype=np.uint8)
    image = shot[50:70, 100:130].copy()
    assert distinct(image, shot, Region(100, 50, 30, 20)) < 0.7


def test_distinct_scores_high_for_a_repeated_image():
    shot = np.random.default_rng(1).integers(0, 255, (200, 300, 3), dtype=np.uint8)
    image = shot[50:70, 100:130].copy()
    shot[150:170, 200:230] = image
    assert distinct(image, shot, Region(100, 50, 30, 20)) > 0.99


def test_item_kinds():
    from darbit.capture import Item

    assert Item.parse("Gui.Play") == Item("Gui.Play", "image")
    assert Item.parse("location:afk/spot") == Item("afk/spot", "location")
    assert Item.parse("region:menus/bag") == Item("menus/bag", "region")


def test_list_file(tmp_path):
    from darbit.capture.common import Item, add_to_list, captured, read_list

    path = tmp_path / "capture.txt"
    path.write_text("# what the bot needs\n\nGui.Play   # lobby: Play button\nlocation: afk/spot\n"
                    "region: menus/bag  # the bag\n", encoding="utf-8")
    items = read_list(path)
    assert items == [Item("Gui.Play"), Item("afk/spot", "location"), Item("menus/bag", "region")]
    assert items[0].note == "lobby: Play button"
    add_to_list(path, Item("Gui.Bag", "image", "lobby: Bag button"))
    assert read_list(path)[-1].note == "lobby: Bag button"
    (tmp_path / "images").mkdir()
    (tmp_path / "images" / "Gui.Play.png").write_bytes(b"")
    assert captured(items[0], tmp_path / "images")
    assert not captured(items[1], tmp_path / "images")


def test_undo_restores_what_was_there(tmp_path):
    from darbit.capture.common import Item, Result
    from darbit.capture.store import save_result, undo
    from darbit.core.geometry import Region

    shot = np.random.default_rng(1).integers(0, 255, (200, 300, 3), dtype=np.uint8)
    (tmp_path / "Old.png").write_bytes(b"before")
    first = save_result(tmp_path, Item("New"), Result(image=Region(10, 10, 30, 20)), shot, Region(0, 0, 300, 200), None)
    second = save_result(tmp_path, Item("Old"), Result(image=Region(50, 50, 30, 20)), shot, Region(0, 0, 300, 200),
                         None)
    assert (tmp_path / "New.png").is_file()
    undo(second)
    undo(first)
    assert not (tmp_path / "New.png").exists()
    assert (tmp_path / "Old.png").read_bytes() == b"before"
    assert not (tmp_path / "Old.json").exists()


def test_list_screens(tmp_path):
    from darbit.capture.common import Item, add_to_list, read_list

    path = tmp_path / "capture.txt"
    path.write_text("[Lobby]\nGui.Play\n\n[Play menu]\nPlay.Raid  # Raid tile\n", encoding="utf-8")
    items = read_list(path)
    assert [(i.name, i.screen) for i in items] == [("Gui.Play", "Lobby"), ("Play.Raid", "Play menu")]
    add_to_list(path, Item("Gui.Bag", "image", "", "Lobby"))
    assert [i.name for i in read_list(path)] == ["Gui.Play", "Gui.Bag", "Play.Raid"]
