import dataclasses
from pathlib import Path

import pytest

from darbit.project.manifest import SETTING_KINDS, ProjectError, find, load, setup, version_matches
from darbit.settings import Settings, settings

MANIFEST = """
[bot]
name = "test-bot"
version = "1.2.0"
darbit = ">=0.2,<0.3"
window = "Roblox"
accent = "#ff7ab6"
captured_at = { size = [2560, 1600], scale = 1.5 }

[settings]
timeout = 5
similarity = 0.9
log = false
logs = "my-logs"

[images]
folders = ["assets/images", "more"]

[keys]
"run.stop" = "ctrl+alt+x"
"""


@pytest.fixture(autouse=True)
def no_log_files(monkeypatch, tmp_path):
    monkeypatch.setattr(settings, "log", False)
    monkeypatch.setattr(settings, "logs", tmp_path / "darbit-logs")


def make(folder: Path, text: str = MANIFEST) -> Path:
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "darbit.toml").write_text(text, encoding="utf-8")
    return folder


def test_find_walks_up_to_the_nearest_manifest(tmp_path):
    project = make(tmp_path / "bot")
    deep = project / "src" / "bot"
    deep.mkdir(parents=True)
    assert find(deep) == project.resolve()
    assert find(project) == project.resolve()


def test_find_without_a_manifest_is_none(tmp_path):
    assert find(tmp_path) is None


def test_load_reads_every_table(tmp_path):
    project = load(make(tmp_path / "bot"))
    assert (project.name, project.version, project.window) == ("test-bot", "1.2.0", "Roblox")
    assert project.captured_at == {"size": [2560, 1600], "scale": 1.5}
    assert project.settings["timeout"] == 5
    assert project.images == ["assets/images", "more"]
    assert project.keys == {"run.stop": "ctrl+alt+x"}


@pytest.mark.parametrize(
    ("text", "message"),
    [
        ('[bot]\nname = "x"\n[colours]\nmain = 1', "unknown key 'colours'"),
        ("[bot]\nversion = '1.0'", r"\[bot\] needs a name"),
        ('[bot]\nname = "x"\nauthor = "me"', r"\[bot\]: unknown key 'author'"),
        ('[bot]\nname = "x"\n[settings]\nspeed = 1', r"\[settings\]: unknown key 'speed'"),
        ('[bot]\nname = "x"\n[settings]\ntimeout = "long"', "timeout should be a number"),
        ('[bot]\nname = "x"\n[settings]\ntimeout = true', "timeout should be a number"),
        ('[bot]\nname = "x"\n[settings]\nlog = 1', "log should be a true or false"),
        ('[bot]\nname = "x"\n[images]\nfolders = "images"', "folders is a list"),
        ("[bot\n", "darbit.toml"),
    ],
)
def test_load_errors_name_the_key(tmp_path, text, message):
    with pytest.raises(ProjectError, match=message):
        load(make(tmp_path / "bot", text))


def test_every_setting_but_images_can_be_set_in_the_manifest():
    names = set()
    for field in dataclasses.fields(Settings):
        names.add(field.name)
    names.discard("images")  # from [images] folders
    assert set(SETTING_KINDS) == names


def test_setup_applies_the_settings_in_order(tmp_path):
    folder = make(tmp_path / "bot").resolve()
    mine = Settings()
    before = list(mine.images)
    project = setup(mine, "0.2.0", start=folder / "src")
    assert project is not None
    assert (mine.timeout, mine.similarity, mine.log) == (5.0, 0.9, False)
    assert mine.window == "Roblox"
    assert mine.logs == folder / "my-logs"
    assert mine.state == folder / ".darbit" / "state"  # the project's own folder when not set
    assert mine.images[:2] == [folder / "assets/images", folder / "more"]
    assert mine.images[2:] == before
    assert mine.glide == Settings().glide  # untouched keys keep darbit's defaults
    mine.timeout = 10  # the script still wins (layer 3)
    assert mine.timeout == 10


def test_setup_without_a_manifest_changes_nothing(tmp_path):
    mine = Settings()
    assert setup(mine, "0.2.0", start=tmp_path) is None
    assert mine == Settings()


def test_setup_warns_when_the_darbit_version_does_not_match(tmp_path):
    folder = make(tmp_path / "bot")
    with pytest.warns(UserWarning, match="wants darbit >=0.2,<0.3, this is darbit 0.4.0"):
        setup(Settings(), "0.4.0", start=folder)


def test_setup_warns_about_a_version_it_cannot_read(tmp_path):
    folder = make(tmp_path / "bot", '[bot]\nname = "x"\ndarbit = "~0.2"')
    with pytest.warns(UserWarning, match="can't read"):
        setup(Settings(), "0.2.0", start=folder)


@pytest.mark.parametrize(
    ("version", "wanted", "result"),
    [
        ("0.2.0", ">=0.2,<0.3", True),
        ("0.2.9", ">=0.2,<0.3", True),
        ("0.3.0", ">=0.2,<0.3", False),
        ("0.1.4", ">=0.2", False),
        ("1.0", "==1.0.0", True),
        ("1.0.0", "!=1.0", False),
        ("0.5.0", ">0.4, <=0.5", True),
        ("0.5.0", "~=0.5", None),
        ("0.5.0rc1", ">=0.5", None),
    ],
)
def test_version_matches(version, wanted, result):
    assert version_matches(version, wanted) is result


def test_a_pre_release_counts_as_its_release():
    assert version_matches("1.0.0.dev0", ">=1.0,<2") is True
    assert version_matches("1.0.0rc1", ">=0.4,<0.5") is False
    assert version_matches("one", ">=1.0") is None
