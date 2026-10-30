"""A bot's own settings: declared in settings.toml, filled in config.toml, edited in darbit Studio's form.

`load_schema` reads settings.toml: a table with a `type` is a setting, any other table is a section of the
form. `load_values` checks the user's config.toml against it (and makes one from the defaults when there's
none) and returns the values, nested like the file. `write_values` saves values back into config.toml, line
by line, so the user's comments and order stay. See docs/archive/tasks/T18-settings-form.md.
"""

import json
import tomllib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

TYPES = ("bool", "int", "float", "str", "choice", "keys", "target", "region", "location", "list")
SETTING_KEYS = {"type", "default", "label", "help", "min", "max", "options"}
SECTION_KEYS = {"label", "help"}


class SettingsError(ValueError):
    """A settings.toml or config.toml that can't be used; the message names the key and the rule."""


@dataclass
class Setting:
    key: str  # "speed_raid.every_minutes"
    type: str
    default: Any = None
    label: str = ""
    help: str = ""
    rules: dict = field(default_factory=dict)  # min, max, options


@dataclass
class Section:
    key: str  # "speed_raid"; "" for settings at the top of the file
    label: str = ""
    help: str = ""
    settings: list[Setting] = field(default_factory=list)


@dataclass
class Schema:
    sections: list[Section] = field(default_factory=list)

    @property
    def settings(self) -> list[Setting]:
        found = []
        for section in self.sections:
            found += section.settings
        return found


# ---- the schema


def load_schema(path: Path) -> Schema:
    """Read and check a settings.toml."""
    try:
        data = tomllib.loads(path.read_text(encoding="utf-8"))
    except tomllib.TOMLDecodeError as error:
        raise SettingsError(f"{path.name}: {error}") from None
    schema = Schema()
    top = Section("")
    schema.sections.append(top)
    _read_table(data, "", top, schema)
    if not top.settings:
        schema.sections.remove(top)
    return schema


def _read_table(table: dict, prefix: str, section: Section, schema: Schema) -> None:
    for name, value in table.items():
        if not isinstance(value, dict):
            continue  # a section's own label and help, read by its caller
        key = prefix + name
        if "type" in value:
            section.settings.append(_read_setting(key, value))
            continue
        for extra in value:
            if not isinstance(value[extra], dict) and extra not in SECTION_KEYS:
                raise SettingsError(f"settings.toml [{key}]: unknown key {extra!r} (a setting needs a type)")
        inner = Section(key, str(value.get("label", name.replace("_", " ").capitalize())), str(value.get("help", "")))
        schema.sections.append(inner)
        _read_table(value, key + ".", inner, schema)


def _read_setting(key: str, data: dict) -> Setting:
    for extra in data:
        if extra not in SETTING_KEYS:
            raise SettingsError(f"settings.toml [{key}]: unknown key {extra!r}")
    kind = data["type"]
    if kind not in TYPES:
        raise SettingsError(f"settings.toml [{key}]: type {kind!r} isn't one of {', '.join(TYPES)}")
    rules = {}
    for rule in ("min", "max", "options"):
        if rule in data:
            rules[rule] = data[rule]
    if kind == "choice" and not rules.get("options"):
        raise SettingsError(f"settings.toml [{key}]: a choice needs options")
    if ("min" in rules or "max" in rules) and kind not in ("int", "float"):
        raise SettingsError(f"settings.toml [{key}]: min and max are for int and float settings")
    label = str(data.get("label", key.rsplit(".", 1)[-1].replace("_", " ").capitalize()))
    setting = Setting(key, kind, data.get("default"), label, str(data.get("help", "")), rules)
    if setting.default is not None:
        problem = check(setting, setting.default)
        if problem:
            raise SettingsError(f"settings.toml [{key}]: the default {problem}")
    return setting


# ---- values


def check(setting: Setting, value: object) -> str:
    """What's wrong with a value for a setting, or "" when it's fine."""
    kind = setting.type
    if kind == "bool" and not isinstance(value, bool):
        return f"should be true or false, not {value!r}"
    if kind == "int" and (isinstance(value, bool) or not isinstance(value, int)):
        return f"should be a whole number, not {value!r}"
    if kind == "float" and (isinstance(value, bool) or not isinstance(value, (int, float))):
        return f"should be a number, not {value!r}"
    if kind in ("str", "keys", "target") and not isinstance(value, str):
        return f"should be text, not {value!r}"
    if kind == "choice" and value not in setting.rules.get("options", []):
        return f"should be one of {setting.rules['options']}, not {value!r}"
    if kind == "region" and not _numbers(value, 4):
        return f"should be [x, y, w, h], not {value!r}"
    if kind == "location" and not _numbers(value, 2):
        return f"should be [x, y], not {value!r}"
    if kind == "list" and not isinstance(value, list):
        return f"should be a list, not {value!r}"
    if "min" in setting.rules and value < setting.rules["min"]:
        return f"should be at least {setting.rules['min']}, not {value!r}"
    if "max" in setting.rules and value > setting.rules["max"]:
        return f"should be at most {setting.rules['max']}, not {value!r}"
    return ""


def _numbers(value: object, count: int) -> bool:
    if not isinstance(value, list) or len(value) != count:
        return False
    for item in value:
        if isinstance(item, bool) or not isinstance(item, (int, float)):
            return False
    return True


def _lookup(data: dict, key: str) -> tuple[bool, object]:
    current: object = data
    for part in key.split("."):
        if not isinstance(current, dict) or part not in current:
            return False, None
        current = current[part]
    return True, current


def _put(data: dict, key: str, value: object) -> None:
    parts = key.split(".")
    current = data
    for part in parts[:-1]:
        current = current.setdefault(part, {})
    current[parts[-1]] = value


def load_values(schema: Schema, config: Path) -> dict:
    """The user's values checked against the schema, nested like the file; config.toml is created from the
    defaults when it's missing. Every problem is listed in one error."""
    if not config.is_file():
        defaults = {}
        for setting in schema.settings:
            if setting.default is not None:
                defaults[setting.key] = setting.default
        write_values(schema, config, defaults)
    try:
        data = tomllib.loads(config.read_text(encoding="utf-8"))
    except tomllib.TOMLDecodeError as error:
        raise SettingsError(f"{config.name}: {error}") from None
    values: dict = {}
    problems = []
    for setting in schema.settings:
        given, value = _lookup(data, setting.key)
        if not given:
            value = setting.default
        elif check(setting, value):
            problems.append(f"{setting.key} {check(setting, value)}")
            continue
        _put(values, setting.key, value)
    if problems:
        raise SettingsError(f"{config.name}: " + "; ".join(problems))
    return values


# ---- writing config.toml, keeping comments


def toml_value(value: object) -> str:
    """A value written as TOML."""
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return repr(value)
    if isinstance(value, str):
        return json.dumps(value, ensure_ascii=False)  # a JSON string is a TOML basic string
    if isinstance(value, list):
        parts = []
        for item in value:
            parts.append(toml_value(item))
        return "[" + ", ".join(parts) + "]"
    raise SettingsError(f"can't write {value!r} to config.toml")


def _comment_start(line: str) -> int:
    """Where a line's comment starts, ignoring # inside strings; -1 when there's none."""
    quote = ""
    for index, character in enumerate(line):
        if quote:
            if character == quote and line[index - 1] != "\\":
                quote = ""
        elif character in "\"'":
            quote = character
        elif character == "#":
            return index
    return -1


def _table_of(line: str) -> str | None:
    text = line.strip()
    if text.startswith("[") and not text.startswith("[[") and "]" in text:
        return text[1 : text.index("]")].strip()
    return None


def write_values(schema: Schema, config: Path, values: dict) -> None:
    """Save values ({"speed_raid.enabled": True} or nested) into config.toml, keeping comments and order."""
    flat = {}
    for setting in schema.settings:
        given, value = _lookup(values, setting.key)
        if not given and setting.key in values:
            given, value = True, values[setting.key]
        if given:
            problem = check(setting, value)
            if problem:
                raise SettingsError(f"{setting.key} {problem}")
            flat[setting.key] = value

    lines = []
    if config.is_file():
        lines = config.read_text(encoding="utf-8").splitlines()
    written = set()
    table = ""
    for index, line in enumerate(lines):
        header = _table_of(line)
        if header is not None:
            table = header
            continue
        name = line.split("=", 1)[0].strip()
        if "=" not in line or not name or name.startswith("#"):
            continue
        key = f"{table}.{name}" if table else name
        if key not in flat:
            continue
        comment = _comment_start(line)
        tail = "  " + line[comment:] if comment >= 0 else ""
        indent = line[: len(line) - len(line.lstrip())]
        lines[index] = f"{indent}{name} = {toml_value(flat[key])}{tail}"
        written.add(key)

    for key, value in flat.items():
        if key in written:
            continue
        table, _, name = key.rpartition(".")
        _insert(lines, table, f"{name} = {toml_value(value)}")

    text = "\n".join(lines).strip("\n") + "\n"
    tomllib.loads(text)  # never leave a file that doesn't read back
    config.parent.mkdir(parents=True, exist_ok=True)
    config.write_text(text, encoding="utf-8")


def _insert(lines: list[str], table: str, entry: str) -> None:
    """Add a key = value line at the end of its table, making the table when there's none."""
    if not table:
        at = 0
        while at < len(lines) and _table_of(lines[at]) is None:
            at += 1
        while at > 0 and not lines[at - 1].strip():
            at -= 1
        lines.insert(at, entry)
        return
    start = None
    for index, line in enumerate(lines):
        if _table_of(line) == table:
            start = index
            break
    if start is None:
        if lines and lines[-1].strip():
            lines.append("")
        lines += [f"[{table}]", entry]
        return
    end = start + 1
    while end < len(lines) and _table_of(lines[end]) is None:
        end += 1
    while end > start + 1 and not lines[end - 1].strip():
        end -= 1
    lines.insert(end, entry)


def as_json(schema: Schema) -> list[dict]:
    """The schema for the Studio's form: sections with their settings."""
    sections = []
    for section in schema.sections:
        settings = []
        for setting in section.settings:
            settings.append(
                {
                    "key": setting.key,
                    "type": setting.type,
                    "default": setting.default,
                    "label": setting.label,
                    "help": setting.help,
                    "rules": setting.rules,
                }
            )
        sections.append({"key": section.key, "label": section.label, "help": section.help, "settings": settings})
    return sections
