"""darbit Studio's requests: the bots, running them, and each bot's Overview, settings, library and runs.

Bots are the installed ones in %LOCALAPPDATA%\\darbit\\bots plus any project folder added by hand. A bot run from
the Studio is its own process (its entry, in its environment), stopped and paused through a control folder
the bot's darbit watches (platform/safety.py), so held keys are always let go. While a bot runs, its run
report is watched and every change goes to the windows as `project.changed`. See docs/tasks/T20-hub.md.
"""

import base64
import json
import os
import subprocess
import threading
import time
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path

import cv2
import numpy as np

from .. import paths
from ..core.targets import IMAGE_TYPES
from ..project import bots
from ..project.manifest import MANIFEST, ProjectError, load
from ..project.settings_schema import SettingsError, as_json, load_schema, load_values, write_values
from . import dashboard, ui_settings
from .events import publish

ADDED = "studio.projects"  # ui setting: project folders added by hand
THUMB = 96  # px, the library's thumbnails
WATCH_EVERY = 1.0  # seconds between looks at a running bot's report
STOP_WAIT = 10.0  # seconds a bot gets to stop before it's ended


@dataclass
class Run:
    """A bot this Studio started."""

    folder: Path
    process: subprocess.Popen
    started: float
    paused: bool = False
    stopping: bool = False  # the Studio asked it to stop, so its Stopped error is a normal end


_runs: dict[str, Run] = {}  # folder -> its run
_lock = threading.Lock()


# ---- finding bots


def project_folders() -> list[Path]:
    """Every bot the Studio knows: installed ones first, then the ones added by hand."""
    found = []
    bots_dir = paths.bots_dir()
    if bots_dir.is_dir():
        for folder in sorted(bots_dir.iterdir()):
            if (folder / MANIFEST).is_file():
                found.append(folder)
    added = ui_settings.get(ADDED, [])
    if isinstance(added, list):
        for text in added:
            folder = Path(str(text))
            if (folder / MANIFEST).is_file() and folder not in found:
                found.append(folder)
    return found


def _folder(data: dict) -> Path:
    """The project folder a request is about; it must be one the Studio knows."""
    folder = Path(str(data.get("path", "")))
    for known in project_folders():
        if known.resolve() == folder.resolve():
            return known
    raise ValueError(f"not a bot darbit Studio knows: {folder}")


def describe(folder: Path) -> dict:
    """A bot for the Studio's switcher: name, version, accent, summary, where it is and whether it runs."""
    try:
        project = load(folder)
    except ProjectError as error:
        return {"path": str(folder), "name": folder.name, "error": str(error), "status": "broken"}
    installed = folder.parent == paths.bots_dir()
    return {
        "path": str(folder),
        "name": project.name,
        "version": project.version,
        "accent": project.accent,
        "summary": project.summary,
        "installed": installed,
        "status": status(folder),
    }


def projects_list(data: dict) -> list[dict]:
    """Installed bots and added project folders."""
    found = []
    for folder in project_folders():
        found.append(describe(folder))
    return found


def project_add(data: dict) -> dict:
    """Add a project folder (one with a darbit.toml) to the Studio."""
    folder = Path(str(data.get("path", ""))).expanduser()
    if not (folder / MANIFEST).is_file():
        raise ValueError(f"no {MANIFEST} in {folder}")
    load(folder)  # a broken manifest is refused now, not later
    added = ui_settings.get(ADDED, [])
    if not isinstance(added, list):
        added = []
    if str(folder) not in added:
        added.append(str(folder))
        ui_settings.set_value(ADDED, added)
    return describe(folder)


# ---- running bots


def control_dir(folder: Path) -> Path:
    return paths.project_dir(folder) / "control"


def status(folder: Path) -> str:
    """running, paused or stopped."""
    with _lock:
        run = _runs.get(str(folder))
    if run is None or run.process.poll() is not None:
        return "stopped"
    if run.paused:
        return "paused"
    return "running"


def running() -> list[Path]:
    """The bots this Studio started that are still running or paused."""
    with _lock:
        runs = list(_runs.values())
    found = []
    for run in runs:
        if run.process.poll() is None:
            found.append(run.folder)
    return found


def stop_all() -> None:
    """Stop every bot this Studio started (quitting darbit)."""
    for folder in running():
        project_stop({"path": str(folder)})


def project_run(data: dict) -> dict:
    """Start a bot as its own process, in its environment, with the Studio's control folder."""
    folder = _folder(data)
    if status(folder) != "stopped":
        raise ValueError(f"{folder.name} is already running")
    project = load(folder)
    control = control_dir(folder)
    control.mkdir(parents=True, exist_ok=True)
    for name in ("stop", "pause"):
        (control / name).unlink(missing_ok=True)
    environment = dict(os.environ)
    environment["DARBIT_CONTROL"] = str(control)
    output = paths.project_dir(folder) / "logs" / "studio-output.log"
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("ab") as sink:
        process = subprocess.Popen(
            bots.entry_command(project.entry, folder), cwd=folder, env=environment, stdout=sink, stderr=sink
        )
    run = Run(folder, process, time.time())
    with _lock:
        _runs[str(folder)] = run
    threading.Thread(target=_watch, args=(run,), name=f"darbit-run-{project.name}", daemon=True).start()
    publish("project.status", {"path": str(folder), "status": "running"})
    return {"status": "running"}


def project_pause(data: dict) -> dict:
    """Pause or resume a bot the Studio started: it lets go of every key and waits at its next darbit call."""
    folder = _folder(data)
    with _lock:
        run = _runs.get(str(folder))
    if run is None or run.process.poll() is not None:
        raise ValueError(f"{folder.name} isn't running")
    pause_file = control_dir(folder) / "pause"
    run.paused = not run.paused
    if run.paused:
        pause_file.write_text("", encoding="utf-8")
    else:
        pause_file.unlink(missing_ok=True)
    publish("project.status", {"path": str(folder), "status": status(folder)})
    return {"status": status(folder)}


def project_stop(data: dict) -> dict:
    """Stop a bot the Studio started, as the stop hotkey would; end it if it doesn't stop in time."""
    folder = _folder(data)
    with _lock:
        run = _runs.get(str(folder))
    if run is None or run.process.poll() is not None:
        return {"status": "stopped"}
    run.stopping = True
    (control_dir(folder) / "pause").unlink(missing_ok=True)
    (control_dir(folder) / "stop").write_text("", encoding="utf-8")
    try:
        run.process.wait(timeout=STOP_WAIT)
    except subprocess.TimeoutExpired:
        run.process.terminate()  # it didn't reach a darbit call in time
    return {"status": "stopped"}


def _watch(run: Run) -> None:
    """Tell the windows when the bot's report changes, and when it ends."""
    last_change = 0.0
    while run.process.poll() is None:
        report = _today_report(run.folder)
        if report.is_file() and report.stat().st_mtime != last_change:
            last_change = report.stat().st_mtime
            publish("project.changed", {"path": str(run.folder)})
        time.sleep(WATCH_EVERY)
    code = run.process.returncode
    ended = "failed"
    if code == 0 or run.stopping:
        ended = "stopped"
    publish("project.status", {"path": str(run.folder), "status": ended, "code": code})
    publish("project.changed", {"path": str(run.folder)})


def _today_report(folder: Path) -> Path:
    project = load(folder)
    return dashboard.report_file(project, datetime.now().strftime("%Y-%m-%d"))


# ---- a bot's pages


def dashboard_tiles(data: dict) -> dict:
    """The Overview: the bot, its status and its tiles for a day (today by default)."""
    folder = _folder(data)
    project = load(folder)
    day = data.get("day") or None
    tiles = []
    for tile in dashboard.tiles(project, day):
        tiles.append(asdict(tile))
    return {"project": describe(folder), "tiles": tiles}


def settings_get(data: dict) -> dict:
    """The bot's settings form: its settings.toml as sections, and the values from config.toml."""
    folder = _folder(data)
    schema_file = folder / "settings.toml"
    if not schema_file.is_file():
        return {"sections": [], "values": {}, "error": None}
    try:
        schema = load_schema(schema_file)
        values = load_values(schema, folder / "config.toml")
    except SettingsError as error:
        return {"sections": [], "values": {}, "error": str(error)}
    flat = {}
    for setting in schema.settings:
        current: object = values
        for part in setting.key.split("."):
            current = current.get(part) if isinstance(current, dict) else None
        flat[setting.key] = current
    return {"sections": as_json(schema), "values": flat, "error": None}


def settings_save(data: dict) -> dict:
    """Save the form's values into config.toml (comments kept); a bad value is refused with its reason."""
    folder = _folder(data)
    schema = load_schema(folder / "settings.toml")
    values = data.get("values") or {}
    write_values(schema, folder / "config.toml", values)
    return {"saved": True}


def library_list(data: dict) -> list[dict]:
    """Every picture in the bot's image folders with a small thumbnail and its last check score."""
    folder = _folder(data)
    project = load(folder)
    scores = _last_scores(folder)
    found = []
    for name in project.images:
        images = folder / name
        if not images.is_dir():
            continue
        for path in sorted(images.iterdir()):
            if path.suffix.lower() not in IMAGE_TYPES:
                continue
            target = path.stem
            found.append({"name": target, "thumbnail": _thumbnail(path), "score": scores.get(target)})
    return found


def _thumbnail(path: Path) -> str | None:
    """A small PNG as a data URL, so the list needs no more requests."""
    pixels = cv2.imdecode(np.fromfile(str(path), dtype=np.uint8), cv2.IMREAD_COLOR)
    if pixels is None:
        return None
    height, width = pixels.shape[:2]
    scale = min(1.0, THUMB / max(height, width))
    if scale < 1.0:
        pixels = cv2.resize(
            pixels, (max(1, round(width * scale)), max(1, round(height * scale))), interpolation=cv2.INTER_AREA
        )
    ok, encoded = cv2.imencode(".png", pixels)
    if not ok:
        return None
    return "data:image/png;base64," + base64.b64encode(encoded.tobytes()).decode("ascii")


def _last_scores(folder: Path) -> dict[str, float]:
    """The newest score per target from `darbit check`'s history."""
    history = paths.project_dir(folder) / "state" / "check.jsonl"
    scores: dict[str, float] = {}
    if not history.is_file():
        return scores
    for line in history.read_text(encoding="utf-8").splitlines():
        try:
            row = json.loads(line)
        except ValueError:
            continue
        name = str(row.get("name", "")).removesuffix(".png")
        if name and isinstance(row.get("score"), (int, float)):
            scores[name] = row["score"]
    return scores


def reports_days(data: dict) -> list[str]:
    """The days the bot has a run report for, newest first."""
    folder = _folder(data)
    project = load(folder)
    logs = dashboard.report_file(project, "x").parent
    days = []
    if logs.is_dir():
        for path in logs.glob("report-*.jsonl"):
            days.append(path.stem.removeprefix("report-"))
    days.sort(reverse=True)
    return days


def tools_open(data: dict) -> dict:
    """Open one of darbit's tools for the bot, in its folder: capture, guide or check."""
    folder = _folder(data)
    tool = str(data.get("tool", ""))
    commands = {
        "capture": ["capture", "--folder", "assets/images"],
        "guide": ["guide", "--folder", "assets/images"],
        "check": ["check", "--folder", "assets/images"],
    }
    if tool not in commands:
        raise ValueError(f"no tool {tool!r} yet")
    project = load(folder)
    if project.images:
        commands[tool][-1] = project.images[0]
    python = bots.entry_command("x.py", folder)[:-1]  # the bot's own Python
    subprocess.Popen([*python, "-m", "darbit.cli", *commands[tool]], cwd=folder)
    return {"opened": tool}


def register() -> None:
    """Add these requests to the server (server/app.py calls it)."""
    from .app import HANDLERS

    HANDLERS["projects.list"] = projects_list
    HANDLERS["project.add"] = project_add
    HANDLERS["project.run"] = project_run
    HANDLERS["project.pause"] = project_pause
    HANDLERS["project.stop"] = project_stop
    HANDLERS["dashboard.tiles"] = dashboard_tiles
    HANDLERS["project.settings"] = settings_get
    HANDLERS["project.settings.save"] = settings_save
    HANDLERS["library.list"] = library_list
    HANDLERS["reports.days"] = reports_days
    HANDLERS["tools.open"] = tools_open
