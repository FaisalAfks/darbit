import tomllib
from pathlib import Path

import pytest

from darbit.capture.guide import GuideError, convert_list, dump, load, parse, progress, steps

DATA = Path(__file__).parent / "data" / "guide"

GUIDE = """
title = "test setup"
say = "Start in the lobby."

[[screen]]
name = "Bag"
say = "Open the Bag."

  [[screen.take]]
  region = "Measure.bag"
  say = "The whole Bag window."

  [[screen.take]]
  image = "Bag.Character"
  in = "Measure.bag"
  point = "center"

[[screen]]
name = "List"

  [[screen.take]]
  images = ["Char.A", "Char.B", "Char.C"]
  order = "list"
"""


def write(folder: Path, text: str) -> Path:
    path = folder / "guide.toml"
    path.write_text(text, encoding="utf-8")
    return path


def test_load_reads_screens_and_items(tmp_path):
    guide = load(write(tmp_path, GUIDE))
    assert guide.title == "test setup"
    assert [s.name for s in guide.screens] == ["Bag", "List"]
    bag = guide.screens[0].take[1]
    assert (bag.kind, bag.names, bag.within, bag.point) == ("image", ["Bag.Character"], "Measure.bag", "center")
    assert guide.screens[1].take[0].order == "list"


def test_steps_list_every_target_in_order(tmp_path):
    found = steps(load(write(tmp_path, GUIDE)))
    assert [s.name for s in found] == ["Measure.bag", "Bag.Character", "Char.A", "Char.B", "Char.C"]
    assert [s.kind for s in found] == ["region", "image", "image", "image", "image"]
    assert found[3].index == 1
    assert found[1].item.screen == "Bag"


@pytest.mark.parametrize(
    ("text", "message"),
    [
        ('title = "x"\ncolour = "red"', "unknown key 'colour'"),
        ('[[screen]]\nsay = "x"', "screen 1: needs a name"),
        ('[[screen]]\nname = "A"\n[[screen.take]]\nsay = "x"', "item 1: needs exactly one of"),
        ('[[screen]]\nname = "A"\n[[screen.take]]\nimage = "X"\nregion = "Y"', "needs exactly one of"),
        ('[[screen]]\nname = "A"\n[[screen.take]]\nimages = []', "images needs a name"),
        (
            '[[screen]]\nname = "A"\n[[screen.take]]\nimage = "X"\n[[screen.take]]\nimage = "X"',
            "X is in the guide twice",
        ),
        ('[[screen]]\nname = "A"\n[[screen.take]]\nimage = "X"\norder = "random"', 'order is "any" or "list"'),
        (
            '[[screen]]\nname = "A"\n[[screen.take]]\nimage = "X"\n[[screen.take]]\nimage = "Y"\nin = "X"',
            "isn't a region",
        ),
        ("title = ", "guide.toml"),
    ],
)
def test_load_errors_say_where(tmp_path, text, message):
    with pytest.raises(GuideError, match=message):
        load(write(tmp_path, text))


def test_in_may_name_a_region_outside_the_guide():
    guide = parse({"screen": [{"name": "A", "take": [{"image": "X", "in": "Elsewhere.region"}]}]})
    assert guide.screens[0].take[0].within == "Elsewhere.region"


def test_progress_counts_saved_files_and_finds_the_next(tmp_path):
    guide = load(write(tmp_path, GUIDE))
    images = tmp_path / "images"
    images.mkdir()
    assert progress(guide, images).current.name == "Measure.bag"

    (images / "Measure.bag.json").write_text("{}", encoding="utf-8")
    (images / "Bag.Character.png").write_bytes(b"")
    (images / "Char.B.png").write_bytes(b"")
    done = progress(guide, images)
    assert (done.done, done.total) == (3, 5)
    assert done.current.name == "Char.A"  # a list is taken top to bottom: A before C, though B is done

    (images / "Char.A.png").write_bytes(b"")
    (images / "Char.C.png").write_bytes(b"")
    assert progress(guide, images).current is None


def test_convert_list_groups_screens_and_long_runs():
    guide = convert_list(DATA / "capture.txt", "test setup")
    assert [s.name for s in guide.screens] == ["Lobby", "Character list"]
    lobby = guide.screens[0].take
    assert [(t.kind, t.names[0]) for t in lobby] == [
        ("image", "Gui.Play"),
        ("image", "Gui.Bag"),
        ("region", "Measure.bagMenu"),
    ]
    assert lobby[0].say == "lobby: the Play button"
    characters, slider = guide.screens[1].take
    assert characters.kind == "images"
    assert characters.order == "list"
    assert characters.names[0] == "SR.Char.Naruto"
    assert len(characters.names) == 6
    assert characters.say == "Speed Raid list"
    assert (slider.kind, slider.names) == ("location", ["Measure.listSlider"])


def test_short_runs_stay_single_images(tmp_path):
    path = tmp_path / "capture.txt"
    path.write_text("[A]\nX.One\nX.Two\nX.Three\n", encoding="utf-8")
    takes = convert_list(path).screens[0].take
    assert [t.kind for t in takes] == ["image", "image", "image"]


def test_dump_reads_back_the_same(tmp_path):
    guide = convert_list(DATA / "capture.txt", 'a "quoted" title')
    guide.screens[0].take[0].point = [4, -2]
    text = dump(guide)
    tomllib.loads(text)
    again = load(write(tmp_path, text))
    assert again == guide


def test_runs_keep_their_notes_when_they_say_more_than_the_name(tmp_path):
    path = tmp_path / "capture.txt"
    lines = ["[Menu]"]
    for name, note in [("Raid", "Raid"), ("DailyRaid", "Raid Challenge"), ("AFK", "AFK"), ("Boss", "Boss"), ("X", "X")]:
        lines.append(f"Play.{name}  # Play menu: {note}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    takes = convert_list(path).screens[0].take
    assert len(takes) == 5
    assert takes[1].say == "Play menu: Raid Challenge"
