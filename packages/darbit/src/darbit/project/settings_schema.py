"""A bot's own settings: declared in settings.toml, filled in config.toml, edited in the hub's form.
See docs/tasks/T18-settings-form.md."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

TYPES = ("bool", "int", "float", "str", "choice", "keys", "target", "region", "location", "list")


@dataclass
class Setting:
    key: str  # "speed_raid.every_minutes"
    type: str
    default: Any = None
    label: str = ""
    help: str = ""
    rules: dict = field(default_factory=dict)  # min, max, options


def load_schema(path: Path) -> list[Setting]:
    raise NotImplementedError("TODO(T18)")


def load_values(schema: list[Setting], config: Path) -> dict:
    """The user's values checked against the schema; config.toml is created from defaults when missing."""
    raise NotImplementedError("TODO(T18)")


def write_values(schema: list[Setting], config: Path, values: dict) -> None:
    """Save the values, keeping the user's comments."""
    raise NotImplementedError("TODO(T18)")
