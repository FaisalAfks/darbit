"""The windows' own settings (the theme, where a bar was dragged to) and a custom theme.

Settings are kept in %APPDATA%\\darbit\\ui.json; a custom theme is %APPDATA%\\darbit\\theme.toml, a flat table
of token names without "--" on top of a base theme: `base = "glass-dark"`, `accent = "#ff7ab6"`.
"""

import json
import threading
import tomllib

from .. import paths

THEMES = ("glass-dark", "glass-light", "midnight", "high-contrast")
_lock = threading.Lock()


def _file():
    return paths.config_dir() / "ui.json"


def read_all() -> dict:
    path = _file()
    if not path.is_file():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}  # a broken file is the same as none: defaults


def get(key: str, default: object = None) -> object:
    return read_all().get(key, default)


def set_value(key: str, value: object) -> None:
    """Save one setting."""
    with _lock:
        values = read_all()
        values[key] = value
        path = _file()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(values, indent=2), encoding="utf-8")


def theme() -> dict:
    """The chosen theme and the custom theme's tokens: {"name": "glass-dark", "tokens": {...} or None}."""
    name = get("ui.theme", THEMES[0])
    if name not in THEMES:
        name = THEMES[0]
    tokens = None
    custom = paths.config_dir() / "theme.toml"
    if custom.is_file():
        try:
            data = tomllib.loads(custom.read_text(encoding="utf-8"))
        except (OSError, tomllib.TOMLDecodeError):
            data = {}
        base = data.pop("base", None)
        if base in THEMES:
            name = base
        tokens = {}
        for key, value in data.items():
            tokens[str(key)] = str(value)
    return {"name": name, "tokens": tokens}
