"""A bot's own settings as one object: `cfg = d.config()` reads `settings.toml` (what each setting is, its default
and limits) and `config.toml` (this PC's values, made from the defaults the first time), checked on every start.

    cfg = d.config()
    if cfg.quests.enabled:
        every = cfg.quests.every_minutes

darbit Studio's Settings page edits the same config.toml.
"""

from pathlib import Path
from types import SimpleNamespace

from ..project.settings_schema import load_schema, load_values


def _as_object(values: dict) -> SimpleNamespace:
    found = SimpleNamespace()
    for key, value in values.items():
        if isinstance(value, dict):
            value = _as_object(value)
        setattr(found, key, value)
    return found


def config(folder: Path | str | None = None) -> SimpleNamespace:
    """The bot's settings, sections as attributes: cfg.section.key. `folder` holds settings.toml and config.toml;
    by default the bot's project folder (where its darbit.toml is). Raises SettingsError listing every bad value."""
    if folder is None:
        from .. import _project

        if _project is None:
            raise FileNotFoundError("no darbit.toml found: pass the folder with settings.toml, d.config(folder)")
        folder = _project.folder
    folder = Path(folder)
    schema = load_schema(folder / "settings.toml")
    return _as_object(load_values(schema, folder / "config.toml"))
