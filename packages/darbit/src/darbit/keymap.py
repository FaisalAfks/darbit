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
RENAMED = {"highlight.toggle": "scout.toggle"}  # old names a keymap may still set


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
            keys.setdefault(scope, {}).update(renamed(actions))
    return keys


def renamed(actions: dict[str, str]) -> dict[str, str]:
    """A layer's keys with old action names under their new ones (a new name set in the same layer wins)."""
    found = {}
    for action, keys in actions.items():
        new = RENAMED.get(action)
        if new is None:
            found[action] = keys
        elif new not in actions:
            found[new] = keys
    return found


def _scope_of(action: str) -> str:
    for scope, actions in defaults().items():
        if action in actions:
            return scope
    raise ValueError(f"no key called {action}")


def _write_user(data: Keymap) -> None:
    lines = []
    for scope, actions in data.items():
        if actions:
            lines.append(f"[{scope}]")
            lines.extend(f'"{action}" = "{keys}"' for action, keys in actions.items())
            lines.append("")
    path = user_file()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8", newline="\n")


def _read_user() -> Keymap:
    path = user_file()
    if not path.is_file():
        return {}
    return tomllib.loads(path.read_text(encoding="utf-8"))


def set_key(action: str, keys: str) -> None:
    """Save the user's keys for an action ("" turns it off)."""
    data = _read_user()
    data.setdefault(_scope_of(action), {})[action] = keys
    _write_user(data)


def reset_key(action: str) -> None:
    """Back to the default keys for an action."""
    data = _read_user()
    scope = data.get(_scope_of(action), {})
    scope.pop(action, None)
    for old, new in RENAMED.items():
        if new == action:
            scope.pop(old, None)  # or the old name would set it again
    _write_user(data)


def combo(action: str, project: Path | None = None) -> str:
    """The keys an action has (`"record.toggle"` -> `"ctrl+alt+r"`), in whichever scope it's listed; "" when none."""
    for scope in load(project).values():
        if action in scope:
            return str(scope[action])
    return ""
