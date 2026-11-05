"""darbit.toml: a bot's name, version, entry, game window, accent, and its darbit settings.
See docs/archive/tasks/T17-projects.md.

`find` walks up from a folder to the nearest darbit.toml, `load` reads and checks it, and `apply` puts its
`[settings]` and `[images]` on darbit's settings (layer 2, before anything the script sets). `setup` does all
three for the running script when darbit is imported; without a darbit.toml nothing changes.
"""

import tomllib
import warnings
from dataclasses import dataclass, field
from pathlib import Path

from .. import paths
from ..runtime.log import log
from ..settings import Settings, script_folder

MANIFEST = "darbit.toml"
TABLES = {"bot", "settings", "images", "keys", "studio", "run"}
BOT_KEYS = {"name", "version", "darbit", "entry", "window", "accent", "captured_at"}
IMAGE_KEYS = {"folders"}
STUDIO_KEYS = {"summary", "tiles"}
RUN_KEYS = {"restart", "keep_days"}
# the tiles darbit Studio can show on a bot's Overview (decision 0011); "progress:<label>" picks one progress
TILES = ("now", "round", "progress", "gains", "next", "activity", "failures", "watching", "setup")

# what each darbit setting takes in [settings]; images come from [images] instead
SPACES = ("screen", "window")  # where targets' places are kept: screen pixels, or the app window's
SETTING_KINDS = {
    "timeout": "number",
    "similarity": "number",
    "glide": "number",
    "scan_rate": "number",
    "screenshot_after": "number",
    "window": "text",
    "stop_key": "text",
    "missing_images": "text",
    "log": "true or false",
    "logs": "folder",
    "state": "folder",
    "matcher": "text",
    "match": "table",  # matching options: [settings.match] fast = true
    "space": "text",  # "screen" (the default) or "window"
    "day_starts": "text",  # when the bot's day starts: "03:00", or "00:00 UTC"
    "polite": "number",  # polite mode: seconds of quiet before the bot goes on after the person used the mouse
}


class ProjectError(ValueError):
    """A darbit.toml that can't be used; the message says which key."""


def _default_images() -> list[str]:
    return ["images"]


@dataclass
class Project:
    folder: Path
    name: str
    version: str = "0.0.0"
    darbit: str = ""  # the darbit versions it needs, e.g. ">=0.5,<0.6"
    entry: str = "bot.py"
    window: str | None = None
    accent: str | None = None
    captured_at: dict | None = None  # the screen its targets were taken on: {size = [w, h], scale = 1.5}
    settings: dict = field(default_factory=dict)  # layer 2 of darbit's settings
    images: list[str] = field(default_factory=_default_images)  # image folders, relative to the project
    keys: dict = field(default_factory=dict)  # keymap overrides
    summary: str = ""  # one line under the bot's name in the Studio
    tiles: list[str] = field(default_factory=list)  # the Overview's tiles in order; empty: the defaults
    restart: int = 0  # [run] restart: times an hour the service starts the bot again after it failed
    keep_days: int = 30  # [run] keep_days: days of run history, reports and logs the service keeps


def find(start: Path) -> Path | None:
    """The nearest folder with a darbit.toml, from `start` upward."""
    folder = start.resolve()
    while True:
        if (folder / MANIFEST).is_file():
            return folder
        if folder.parent == folder:
            return None
        folder = folder.parent


def load(folder: Path) -> Project:
    """Read and check a project's darbit.toml."""
    path = folder / MANIFEST
    try:
        data = tomllib.loads(path.read_text(encoding="utf-8"))
    except tomllib.TOMLDecodeError as error:
        raise ProjectError(f"{path}: {error}") from None
    _check_keys(data, TABLES, MANIFEST)

    bot = data.get("bot", {})
    _check_keys(bot, BOT_KEYS, "[bot]")
    if not bot.get("name"):
        raise ProjectError(f"{path}: [bot] needs a name")
    settings = data.get("settings", {})
    _check_keys(settings, set(SETTING_KINDS), "[settings]")
    for key, value in settings.items():
        _check_setting(key, value)
    images = data.get("images", {})
    _check_keys(images, IMAGE_KEYS, "[images]")
    folders = images.get("folders", ["images"])
    if not isinstance(folders, list) or not all(isinstance(f, str) for f in folders):
        raise ProjectError('[images] folders is a list of folder names, e.g. ["images"]')
    studio = data.get("studio", {})
    _check_keys(studio, STUDIO_KEYS, "[studio]")
    tiles = studio.get("tiles", [])
    _check_tiles(tiles)
    run = data.get("run", {})
    _check_keys(run, RUN_KEYS, "[run]")
    restart = run.get("restart", 0)
    if not isinstance(restart, int) or isinstance(restart, bool) or restart < 0:
        raise ProjectError(f"{MANIFEST} [run]: restart is how many times an hour to start the bot again, e.g. 3")
    keep_days = run.get("keep_days", 30)
    if not isinstance(keep_days, int) or isinstance(keep_days, bool) or keep_days < 1:
        raise ProjectError(f"{MANIFEST} [run]: keep_days is how many days of history to keep, e.g. 30")

    return Project(
        folder=folder,
        name=bot["name"],
        version=bot.get("version", "0.0.0"),
        darbit=bot.get("darbit", ""),
        entry=bot.get("entry", "bot.py"),
        window=bot.get("window"),
        accent=bot.get("accent"),
        captured_at=bot.get("captured_at"),
        settings=settings,
        images=folders,
        keys=data.get("keys", {}),
        summary=str(studio.get("summary", "")),
        tiles=tiles,
        restart=restart,
        keep_days=keep_days,
    )


def _check_tiles(tiles: object) -> None:
    if not isinstance(tiles, list):
        raise ProjectError(f'{MANIFEST} [studio]: tiles is a list, e.g. ["now", "progress", "activity"]')
    for tile in tiles:
        kind = str(tile).split(":", 1)[0]
        if kind not in TILES:
            raise ProjectError(f"{MANIFEST} [studio]: unknown tile {tile!r}; tiles are {', '.join(TILES)}")


def _check_keys(data: dict, allowed: set[str], where: str) -> None:
    for key in data:
        if key not in allowed:
            raise ProjectError(f"{MANIFEST} {where}: unknown key {key!r}")


def _check_setting(key: str, value: object) -> None:
    kind = SETTING_KINDS[key]
    if kind == "number":
        ok = isinstance(value, (int, float)) and not isinstance(value, bool)
    elif kind == "true or false":
        ok = isinstance(value, bool)
    elif kind == "table":
        ok = isinstance(value, dict)
    else:
        ok = isinstance(value, str)
    if not ok:
        raise ProjectError(f"{MANIFEST} [settings]: {key} should be a {kind}, not {value!r}")
    if key == "space" and value not in SPACES:
        raise ProjectError(f'{MANIFEST} [settings]: space is "screen" or "window", not {value!r}')
    if key == "day_starts":
        from .. import days

        try:
            days.parse(value)
        except ValueError as error:
            raise ProjectError(f"{MANIFEST} [settings]: {error}") from None


def apply(project: Project, settings: Settings) -> list[str]:
    """Put the project's settings on darbit's settings. Returns what changed, as `key = value` lines."""
    changed = []
    # the project's own runtime folder, unless [settings] names others
    settings.logs = paths.project_dir(project.folder) / "logs"
    settings.state = paths.project_dir(project.folder) / "state"
    if project.window is not None:
        settings.window = project.window
        changed.append(f"window = {project.window}")
    for key, value in project.settings.items():
        if SETTING_KINDS[key] == "folder":
            value = project.folder / value
        elif SETTING_KINDS[key] == "number":
            value = float(value)
        setattr(settings, key, value)
        changed.append(f"{key} = {value}")

    folders = []
    for name in project.images:
        folders.append(project.folder / name)
    for folder in settings.images:
        if folder not in folders:
            folders.append(folder)
    settings.images = folders
    return changed


def version_matches(version: str, wanted: str) -> bool | None:
    """Whether `version` meets `wanted` (">=0.5,<0.6"); None when `wanted` can't be read."""
    have = _numbers(version)
    for clause in wanted.split(","):
        clause = clause.strip()
        if not clause:
            continue
        op = ""
        for candidate in (">=", "<=", "==", "!=", ">", "<"):
            if clause.startswith(candidate):
                op = candidate
                break
        if not op:
            return None
        need = _numbers(clause[len(op) :].strip())
        if have is None or need is None:
            return None
        if not _compare(have, op, need):
            return False
    return True


def _numbers(version: str) -> tuple[int, ...] | None:
    """`0.5.1` -> (0, 5, 1), padded to three numbers; a pre-release counts as its release (`1.0.0.dev0`, `1.0.0rc1`
    -> (1, 0, 0)); None for anything else."""
    parts = version.split(".")
    numbers = []
    for part in parts:
        digits = ""
        for character in part:
            if not character.isdigit():
                break
            digits += character
        if not digits:
            if numbers:
                break  # .dev0, .post1: what comes after the release
            return None
        numbers.append(int(digits))
        if digits != part:
            break  # 0rc1, 0a2
    while len(numbers) < 3:
        numbers.append(0)
    return tuple(numbers)


def _compare(have: tuple[int, ...], op: str, need: tuple[int, ...]) -> bool:
    if op == ">=":
        return have >= need
    if op == "<=":
        return have <= need
    if op == ">":
        return have > need
    if op == "<":
        return have < need
    if op == "==":
        return have == need
    return have != need


def setup(settings: Settings, version: str, start: Path | None = None) -> Project | None:
    """Find the running script's project and apply it. None, and nothing changed, without a darbit.toml."""
    if start is None:
        start = script_folder()
    folder = find(start)
    if folder is None:
        return None
    project = load(folder)
    changed = apply(project, settings)
    log(f"{project.name}: settings from {folder / MANIFEST}: {', '.join(changed) or 'none'}")
    if project.darbit:
        matches = version_matches(version, project.darbit)
        if matches is False:
            _warn(f"{project.name} wants darbit {project.darbit}, this is darbit {version}")
        elif matches is None:
            _warn(f'{MANIFEST}: can\'t read darbit = "{project.darbit}"; write it like ">=0.5,<0.6"')
    return project


def _warn(message: str) -> None:
    log(message)
    warnings.warn(message, stacklevel=3)
