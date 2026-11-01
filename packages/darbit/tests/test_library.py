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
