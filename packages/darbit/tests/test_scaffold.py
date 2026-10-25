"""The parts still being built import without the `app` extra, and their written pieces work."""
import importlib

import pytest

from darbit import keymap
from darbit.server import events
from darbit.server.protocol import MESSAGES

MODULES = [
    "darbit.keymap", "darbit.cli", "darbit.ui",
    "darbit.server", "darbit.server.app", "darbit.server.events", "darbit.server.protocol", "darbit.server.hub",
    "darbit.desktop", "darbit.capture.engine", "darbit.capture.guide", "darbit.capture.service",
    "darbit.runtime.highlight", "darbit.runtime.capture_api",
    "darbit.runs", "darbit.runs.recorder", "darbit.runs.player",
    "darbit.platform.hooks", "darbit.platform.hotkeys", "darbit.platform.dxgi",
    "darbit.project", "darbit.project.settings_schema",
]


@pytest.mark.parametrize("name", MODULES)
def test_imports_without_the_ui_extra(name):
    importlib.import_module(name)


def test_the_default_keymap_has_every_scope():
    keys = keymap.defaults()
    assert {"global", "app", "capture", "run_panel", "hub", "mouse"} <= keys.keys()
    assert keys["global"]["run.stop"] == "ctrl+alt+q"
    assert all(k.startswith("ctrl+alt+") for k in keys["global"].values())  # games rarely use ctrl+alt


def test_a_users_keymap_overrides_the_defaults(tmp_path, monkeypatch):
    monkeypatch.setattr(keymap.paths, "config_dir", lambda: tmp_path / "darbit")
    (tmp_path / "darbit").mkdir()
    (tmp_path / "darbit" / "keymap.toml").write_text('[global]\n"capture.freeze" = "ctrl+alt+x"\n')
    project = tmp_path / "bot"
    project.mkdir()
    (project / "darbit.toml").write_text('[keys.global]\n"run.stop" = "ctrl+alt+s"\n')
    keys = keymap.load(project)
    assert keys["global"]["capture.freeze"] == "ctrl+alt+x"
    assert keys["global"]["run.stop"] == "ctrl+alt+s"
    assert keys["global"]["record.toggle"] == "ctrl+alt+r"


def test_events_reach_listeners_and_a_broken_one_is_skipped():
    got = []
    stop_broken = events.listen(lambda topic, data: 1 / 0)
    stop = events.listen(lambda topic, data: got.append((topic, data)))
    events.publish("log", {"line": "hi"})
    stop()
    stop_broken()
    events.publish("log", {"line": "nobody"})
    assert got == [("log", {"line": "hi"})]


def test_every_message_is_a_request_or_an_event():
    assert all(kind in ("req", "evt") for kind, _, _ in MESSAGES.values())


def test_every_action_the_ui_names_is_in_the_keymap():
    import re
    from pathlib import Path

    keys = keymap.defaults()
    ui = Path(__file__).parents[2] / "ui" / "src"  # packages/ui/src
    named = set()
    for file in [*ui.rglob("*.svelte"), *ui.rglob("*.ts")]:
        named |= set(re.findall(r'action="([a-z_.]+)"', file.read_text(encoding="utf-8")))

    def known(action: str) -> bool:
        scope, _, rest = action.partition(".")
        return action in keys["global"] or action in keys["app"] or rest in keys.get(scope, {})

    assert named and not [a for a in named if not known(a)]
