"""darbit's modules import without anything extra, and the keymap reads its defaults and overrides."""

import importlib

import pytest

from darbit import keymap

MODULES = [
    "darbit.keymap",
    "darbit.cli",
    "darbit.server",
    "darbit.server.events",
    "darbit.server.hub",
    "darbit.capture",
    "darbit.capture.engine",
    "darbit.capture.guide",
    "darbit.capture.service",
    "darbit.runs",
    "darbit.runs.recorder",
    "darbit.runs.player",
    "darbit.platform.hooks",
    "darbit.platform.hotkeys",
    "darbit.project",
    "darbit.project.settings_schema",
]


@pytest.mark.parametrize("name", MODULES)
def test_every_module_imports(name):
    importlib.import_module(name)


def test_the_default_keymap_has_every_scope():
    keys = keymap.defaults()
    assert {"global", "app", "capture", "run_panel", "hub", "mouse"} <= keys.keys()
    assert keys["global"]["run.stop"] == "ctrl+alt+q"
    assert all(k.startswith("ctrl+alt+") for k in keys["global"].values())  # games rarely use ctrl+alt


def test_a_users_keymap_overrides_the_defaults(tmp_path, monkeypatch):
    def config_dir():
        return tmp_path / "darbit"

    monkeypatch.setattr(keymap.paths, "config_dir", config_dir)
    (tmp_path / "darbit").mkdir()
    (tmp_path / "darbit" / "keymap.toml").write_text('[global]\n"capture.freeze" = "ctrl+alt+x"\n')
    project = tmp_path / "bot"
    project.mkdir()
    (project / "darbit.toml").write_text('[keys.global]\n"run.stop" = "ctrl+alt+s"\n')
    keys = keymap.load(project)
    assert keys["global"]["capture.freeze"] == "ctrl+alt+x"
    assert keys["global"]["run.stop"] == "ctrl+alt+s"
    assert keys["global"]["record.toggle"] == "ctrl+alt+r"
