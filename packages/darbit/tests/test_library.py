"""The Library: every kind of asset, where each is used, and renames that change everything or nothing."""

import json

import cv2
import numpy as np
import pytest

from darbit.project.manifest import load
from darbit.server import library

BOT_CODE = """import darbit as d
from .images import img

d.click(img.Lobby.Play)
d.wait("Lobby.Play.png")
d.click(img.Lobby.PlayButton)  # another asset, must not change
"""


@pytest.fixture
def project(tmp_path):
    (tmp_path / "darbit.toml").write_text(
        '[bot]\nname = "test-bot"\n[images]\nfolders = ["assets/images"]\n', encoding="utf-8"
    )
    images = tmp_path / "assets" / "images"
    images.mkdir(parents=True)
    picture = np.full((40, 400, 3), 180, np.uint8)
    cv2.imwrite(str(images / "Lobby.Play.png"), picture)
    (images / "Lobby.Play.json").write_text(json.dumps({"similarity": 0.85}), encoding="utf-8")
    cv2.imwrite(str(images / "Lobby.PlayButton.png"), picture)
    (images / "Lobby.Menu.json").write_text(json.dumps({"region": [0, 0, 100, 50]}), encoding="utf-8")
    (images / "Fight.Slot.json").write_text(json.dumps({"location": [10, 20]}), encoding="utf-8")
    code = tmp_path / "src" / "test_bot"
    code.mkdir(parents=True)
    (code / "bot.py").write_bytes(BOT_CODE.replace("\n", "\r\n").encode("utf-8"))  # Windows line endings stay
    (tmp_path / ".venv" / "lib").mkdir(parents=True)
    (tmp_path / ".venv" / "lib" / "other.py").write_text("Lobby.Play", encoding="utf-8")  # not the bot's code
    (tmp_path / "guide.toml").write_text(
        'title = "Setup"\n\n[[screen]]\nname = "Lobby"\n\n[[screen.take]]\nimage = "Lobby.Play"\n\n'
        '[[screen.take]]\nimage = "Lobby.Close"\n',
        encoding="utf-8",
    )
    return load(tmp_path)


def by_name(entries):
    found = {}
    for entry in entries:
        found[entry["name"]] = entry
    return found


def test_every_kind_of_asset_is_listed(project):
    assets = by_name(library.assets(project))
    play = assets["Lobby.Play"]
    assert play["kind"] == "image"
    assert play["group"] == "Lobby"
    assert play["similarity"] == 0.85
    assert play["size"] == [400, 40]
    assert play["thumbnail"].startswith("data:image/png;base64,")
    assert assets["Lobby.Menu"]["kind"] == "region"
    assert assets["Fight.Slot"]["kind"] == "location"
    assert assets["Lobby.Close"]["missing"] is True  # in the guide, not taken yet
    assert play["uses"] == 3  # two lines of code and the guide, not the longer name nor .venv


def test_uses_name_the_lines(project):
    found = library.uses(project, "Lobby.Play")
    lines = []
    for use in found:
        lines.append((use.file.name, use.line))
    assert ("bot.py", 4) in lines
    assert ("bot.py", 5) in lines
    assert ("guide.toml", 7) in lines
    assert ("bot.py", 6) not in lines


def test_a_rename_is_shown_before_it_happens(project):
    plan = library.rename_plan(project, "Lobby.Play", "Lobby.Start")
    assert {"from": "Lobby.Play.png", "to": "Lobby.Start.png"} in plan["files"]
    befores = []
    for line in plan["lines"]:
        befores.append(line["after"])
    assert "d.click(img.Lobby.Start)" in befores
    assert (project.folder / "assets" / "images" / "Lobby.Play.png").is_file()  # nothing changed yet


def test_a_rename_changes_files_and_every_line(project):
    library.rename(project, "Lobby.Play", "Lobby.Start")
    images = project.folder / "assets" / "images"
    assert (images / "Lobby.Start.png").is_file()
    assert (images / "Lobby.Start.json").is_file()
    assert not (images / "Lobby.Play.png").exists()
    code = (project.folder / "src" / "test_bot" / "bot.py").read_bytes().decode("utf-8")
    assert "img.Lobby.Start)" in code
    assert '"Lobby.Start.png"' in code
    assert "img.Lobby.PlayButton" in code  # the longer name is left alone
    assert "\r\n" in code  # line endings kept
    assert 'image = "Lobby.Start"' in (project.folder / "guide.toml").read_text(encoding="utf-8")
    assert (project.folder / ".venv" / "lib" / "other.py").read_text(encoding="utf-8") == "Lobby.Play"


def test_a_rename_moves_the_box_on_the_screen_it_was_taken_on(project):
    from darbit.capture.service import screens_folder

    screens = screens_folder(project.folder)
    screens.mkdir(parents=True)
    lobby = {
        "w": 800,
        "h": 600,
        "shot": "a",
        "assets": {
            "Lobby.Play": {"kind": "image", "box": [1, 2, 3, 4]},
            "Lobby.PlayButton": {"kind": "image", "box": [5, 6, 7, 8]},
        },
    }
    fight = {"w": 800, "h": 600, "shot": "b", "assets": {"Fight.Slot": {"kind": "location", "box": [9, 9, 12, 12]}}}
    (screens / "Lobby.json").write_text(json.dumps(lobby), encoding="utf-8")
    (screens / "Fight.json").write_text(json.dumps(fight), encoding="utf-8")
    library.rename(project, "Lobby.Play", "Lobby.Start")
    kept = json.loads((screens / "Lobby.json").read_text(encoding="utf-8"))
    assert list(kept["assets"]) == ["Lobby.Start", "Lobby.PlayButton"]  # the same place in the list
    assert kept["assets"]["Lobby.Start"] == {"kind": "image", "box": [1, 2, 3, 4]}
    assert kept["shot"] == "a"
    assert json.loads((screens / "Fight.json").read_text(encoding="utf-8")) == fight  # the control: untouched
    library.rename(project, "Fight.Slot", "Fight.Seat")  # the screens' places go with a rename of any kind
    assert list(json.loads((screens / "Fight.json").read_text(encoding="utf-8"))["assets"]) == ["Fight.Seat"]


@pytest.mark.parametrize(
    ("old", "new", "message"),
    [
        ("Lobby.Play", "Lobby.PlayButton", "already an asset"),
        ("Lobby.Play", "1bad", "isn't a name"),
        ("Lobby.Play", "Lobby.Play", "same name"),
        ("Nope", "Other", "no asset"),
    ],
)
def test_a_rename_that_cant_work_says_why(project, old, new, message):
    with pytest.raises(library.LibraryError, match=message):
        library.rename_plan(project, old, new)


def test_one_asset_and_only_the_thumbnails_that_changed(project):
    first = by_name(library.assets(project))
    have = {"Lobby.Play": first["Lobby.Play"]["version"], "Lobby.PlayButton": "an older version"}
    again = by_name(library.assets(project, have=have))
    assert again["Lobby.Play"]["same"] is True and again["Lobby.Play"]["thumbnail"] is None  # the page has it
    assert again["Lobby.PlayButton"]["thumbnail"].startswith("data:image/png;base64,")  # changed: sent again
    only = library.assets(project, names={"Lobby.Play", "Lobby.Close"})
    assert [entry["name"] for entry in only] == ["Lobby.Close", "Lobby.Play"]


def test_deleting_an_asset_takes_its_files(project):
    found = library.delete(project, "Lobby.Play")
    assert sorted(found["files"]) == ["assets/images/Lobby.Play.json", "assets/images/Lobby.Play.png"]
    assert by_name(library.assets(project))["Lobby.Play"]["missing"] is True  # the guide still wants it
    with pytest.raises(library.LibraryError):
        library.delete(project, "Lobby.Play")


def test_undo_puts_the_last_deleted_asset_back(project):
    from darbit.server import deleted

    images = project.folder / "assets" / "images"
    before = (images / "Lobby.Play.png").read_bytes()
    library.delete(project, "Lobby.Play")
    assert deleted.take_back(project.folder) == {
        "kind": "asset",
        "name": "Lobby.Play",
        "files": [str(images / "Lobby.Play.png"), str(images / "Lobby.Play.json")],
    }
    assert (images / "Lobby.Play.png").read_bytes() == before
    assert json.loads((images / "Lobby.Play.json").read_text(encoding="utf-8")) == {"similarity": 0.85}
    with pytest.raises(ValueError, match="nothing deleted"):  # put back once
        deleted.take_back(project.folder)


def test_only_the_last_delete_is_kept_and_a_name_taken_again_stays(project):
    from darbit.server import deleted

    images = project.folder / "assets" / "images"
    library.delete(project, "Lobby.Play")
    library.delete(project, "Lobby.Menu")
    assert deleted.take_back(project.folder)["name"] == "Lobby.Menu"
    assert not (images / "Lobby.Play.png").exists()  # the one before is gone for good
    library.delete(project, "Fight.Slot")
    (images / "Fight.Slot.json").write_text("{}", encoding="utf-8")  # taken again since
    with pytest.raises(ValueError, match="there again"):
        deleted.take_back(project.folder)
    assert (images / "Fight.Slot.json").read_text(encoding="utf-8") == "{}"


def test_a_target_names_its_kind_and_old_files_get_it_written(project):
    import json

    from darbit.core.targets import kind_of

    assert kind_of({"kind": "region", "location": [1, 2]}, False) == "region"  # named: taken as it is
    assert kind_of({}, True) == "image"  # an image: the whole screen, clicked at its centre
    assert kind_of({"region": [0, 0, 5, 5]}, False) == "region"
    assert kind_of({"location": [3, 4]}, False) == "location"
    written = library.write_kinds(project)
    assert "Lobby.Play" in written and "Fight.Slot" in written
    images = project.folder / "assets" / "images"
    assert json.loads((images / "Fight.Slot.json").read_text(encoding="utf-8"))["kind"] == "location"
    assert json.loads((images / "Lobby.Play.json").read_text(encoding="utf-8"))["kind"] == "image"
    assert library.write_kinds(project) == []  # named now


def test_an_image_is_tagged_only_as_an_image():
    # a region is a place of its own that images name; an image's location is its click point
    assert library.tags_of("image", {"region": "Bag.Menu", "offset": [4, 0]}) == ["image"]
    assert library.tags_of("region", {"region": [0, 0, 9, 9]}) == ["region"]
    assert library.tags_of("location", {"location": [1, 2]}) == ["location"]


def test_an_image_needs_its_own_similarity_else_the_bots(project, tmp_path):
    from darbit.studio.scout import targets_of

    toml = tmp_path / "darbit.toml"
    toml.write_text(toml.read_text(encoding="utf-8") + "[settings]\nsimilarity = 0.8\n", encoding="utf-8")
    assets = by_name(library.assets(load(tmp_path)))
    assert assets["Lobby.Play"]["needs"] == 0.85  # its own
    assert assets["Lobby.PlayButton"]["needs"] == 0.8  # the bot's, as the bot itself goes by
    needs = {}
    for target in targets_of(tmp_path):
        needs[target.name] = target.similarity
    assert needs == {"Lobby.Play": 0.85, "Lobby.PlayButton": 0.8}  # Scout too
