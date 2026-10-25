"""Every shortcut in darbit, from keymap.toml, with the user's and the project's overrides.

    keymap.load()                       # {"global": {"capture.freeze": "ctrl+alt+c", ...}, "capture": {...}, ...}
    keymap.load(project=Path("my-bot")) # with my-bot/darbit.toml [keys] on top

The web UI gets the same table from the local server (GET /keymap), so a key changed here
changes in every window, the hub and the IDE extension. See docs/tasks/T04-keymap.md.
"""
from __future__ import annotations

import os
import tomllib
from pathlib import Path

DEFAULTS = Path(__file__).with_name("keymap.toml")
Keymap = dict[str, dict[str, str]]  # scope -> action -> keys


def defaults() -> Keymap:
    return tomllib.loads(DEFAULTS.read_text(encoding="utf-8"))


def user_file() -> Path:
    return Path(os.environ.get("APPDATA", Path.home())) / "darbit" / "keymap.toml"


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


def conflicts(keys: Keymap) -> list[tuple[str, str, str]]:
    """Pairs of actions with the same keys where both can fire at once: (keys, action, other action).

    Global keys clash with every scope; other scopes only clash inside themselves."""
    raise NotImplementedError("TODO(T04)")


def normalise(keys: str) -> str:
    """One spelling for a key combination: "Alt+Ctrl+C" -> "ctrl+alt+c" (modifiers in the order ctrl, shift,
    alt, win)."""
    raise NotImplementedError("TODO(T04)")
