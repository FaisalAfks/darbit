"""Every shortcut in darbit, from keymap.toml, with the user's and the project's overrides.

    keymap.load()                       # {"global": {"capture.freeze": "ctrl+alt+c", ...}, "capture": {...}, ...}
    keymap.load(project=Path("my-bot")) # with my-bot/darbit.toml [keys] on top

The Studio reads the same table, so a key changed here changes everywhere it is shown.
"""

import tomllib
from pathlib import Path

from . import paths

DEFAULTS = Path(__file__).with_name("keymap.toml")
Keymap = dict[str, dict[str, str]]  # scope -> action -> keys


def defaults() -> Keymap:
    return tomllib.loads(DEFAULTS.read_text(encoding="utf-8"))


def user_file() -> Path:
    return paths.config_dir() / "keymap.toml"


def load(project: Path | None = None) -> Keymap:
    """The defaults, then the user's keymap.toml, then the project's [keys]. Later wins."""
    keys = defaults()
    layers = [user_file()]
    if project is not None:
        layers.append(project / "darbit.toml")
    for path in layers:
        if not path.is_file():
            continue
        data = tomllib.loads(path.read_text(encoding="utf-8"))
        data = data.get("keys", {}) if path.name == "darbit.toml" else data
        for scope, actions in data.items():
            keys.setdefault(scope, {}).update(actions)
    return keys


def combo(action: str, project: Path | None = None) -> str:
    """The keys an action has (`"record.toggle"` -> `"ctrl+alt+r"`), in whichever scope it's listed; "" when none."""
    for scope in load(project).values():
        if action in scope:
            return str(scope[action])
    return ""
