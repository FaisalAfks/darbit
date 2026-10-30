"""darbit Studio's requests: the bots, running them, and each bot's Overview, settings, library and runs.

Bots are the installed ones in %LOCALAPPDATA%\\darbit\\bots plus any project folder added by hand. A bot run from
the Studio is its own process (its entry, in its environment), stopped and paused through a control folder
the bot's darbit watches (platform/safety.py), so held keys are always let go. While a bot runs, its run
report is watched and every change goes to the windows as `project.changed`. See docs/archive/tasks/T20-hub.md.
"""

import os
import subprocess
import threading
import time
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path

from .. import paths
from ..project import bots
from ..project.manifest import MANIFEST, Project, ProjectError, load
from ..project.settings_schema import SettingsError, as_json, load_schema, load_values, write_values
from . import dashboard, library, results, ui_settings
from .events import publish

ADDED = "studio.projects"  # ui setting: project folders added by hand
WATCH_EVERY = 2.0  # seconds between looks at a running bot's report
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


class Earlier:
    """A bot an earlier Studio started that's still running (that Studio was closed): enough of a Popen for
    status, Stop and the watcher, found through the pid file in the bot's control folder."""

    def __init__(self, pid: int) -> None:
        self.pid = pid
        self.returncode: int | None = None

    def poll(self) -> int | None:
        if self.returncode is None and not _alive(self.pid):
            self.returncode = 0
        return self.returncode

    def wait(self, timeout: float | None = None) -> int:
        deadline = time.monotonic() + (timeout or 0)
        while self.poll() is None:
            if timeout is not None and time.monotonic() >= deadline:
                raise subprocess.TimeoutExpired(str(self.pid), timeout)
            time.sleep(0.2)
        return self.returncode or 0


def _alive(pid: int) -> bool:
    import ctypes

    kernel32 = ctypes.windll.kernel32
    handle = kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid)
    if not handle:
        return False
    code = ctypes.c_ulong()
    try:
        kernel32.GetExitCodeProcess(handle, ctypes.byref(code))
    finally:
        kernel32.CloseHandle(handle)
    return code.value == STILL_ACTIVE


PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
STILL_ACTIVE = 259


def _adopt(folder: Path) -> Run | None:
    """A run an earlier Studio left behind, if its process is still alive."""
    pid_file = control_dir(folder) / "pid"
    try:
        pid = int(pid_file.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    if not _alive(pid):
        pid_file.unlink(missing_ok=True)
        return None
    run = Run(folder, Earlier(pid), pid_file.stat().st_mtime)
    with _lock:
        _runs[str(folder)] = run
    threading.Thread(target=_watch, args=(run,), name=f"darbit-run-{folder.name}", daemon=True).start()
    return run


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
    if run is None:
        run = _adopt(folder)  # started by a Studio that's gone
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
    (control / "pid").write_text(str(process.pid), encoding="utf-8")  # a later Studio can still stop it
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
    if not understands_control(folder):
        raise ValueError(
            f"{folder.name}'s darbit is older than the Studio's Pause: move its darbit pin to a newer release"
        )
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
    if run is None:
        run = _adopt(folder)
    if run is None or run.process.poll() is not None:
        return {"status": "stopped"}
    run.stopping = True
    (control_dir(folder) / "pause").unlink(missing_ok=True)
    (control_dir(folder) / "stop").write_text("", encoding="utf-8")
    wait = STOP_WAIT
    if not understands_control(folder):
        wait = 0  # its darbit is older than the Studio's stop: it would never see it
    try:
        run.process.wait(timeout=wait)
    except subprocess.TimeoutExpired:
        end_tree(run.process.pid)  # it didn't reach a darbit call in time
        from ..platform import input as device

        device.let_go_of_everything()  # whatever it held stays down otherwise
    return {"status": "stopped"}


def end_tree(pid: int) -> None:
    """End a process and every process it started: `uv run` starts the bot as a child, which outlives its parent
    on Windows if only the parent is ended."""
    subprocess.run(["taskkill", "/PID", str(pid), "/T", "/F"], capture_output=True, check=False)


def understands_control(folder: Path) -> bool:
    """Whether the darbit in the bot's own environment takes the Studio's pause and stop (its control folder).
    A bot without its own environment runs with the Studio's darbit, which does."""
    safety = folder / ".venv" / "Lib" / "site-packages" / "darbit" / "platform" / "safety.py"
    if not safety.is_file():
        return True
    try:
        return "DARBIT_CONTROL" in safety.read_text(encoding="utf-8")
    except OSError:
        return True


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
    (control_dir(run.folder) / "pid").unlink(missing_ok=True)
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
    key = _tiles_key(project, day)
    if _tiles_made.get(str(folder), (None, None))[0] != key:
        tiles = []
        for tile in dashboard.tiles(project, day):
            tiles.append(asdict(tile))
        _tiles_made[str(folder)] = (key, tiles)
    return {"project": describe(folder), "tiles": _tiles_made[str(folder)][1]}


_tiles_made: dict[str, tuple[tuple, list[dict]]] = {}  # the Overview's tiles, made again only when something changed


def _tiles_key(project: Project, day: str | None) -> tuple:
    """What the tiles depend on: the report, the minute (next up counts down), the guide and the pictures."""
    report = dashboard.report_file(project, day or datetime.now().strftime("%Y-%m-%d"))
    parts: list = [day, datetime.now().strftime("%H:%M")]
    for path in [report, project.folder / "guide.toml", *library._folders(project)]:
        try:
            stat = path.stat()
            parts.append((stat.st_mtime_ns, stat.st_size))
        except OSError:
            parts.append(None)
    return tuple(parts)


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
    """Every asset the bot uses: images, regions, points, and the guide's pictures still missing."""
    names = data.get("names")
    if names is not None:
        names = set(names)
    have = data.get("have")
    if not isinstance(have, dict):
        have = None
    return library.assets(load(_folder(data)), names, have)


def library_uses(data: dict) -> list[dict]:
    """Every line in the bot's code and guide that names an asset."""
    project = load(_folder(data))
    found = []
    for use in library.uses(project, str(data.get("name", ""))):
        found.append({"file": use.file.relative_to(project.folder).as_posix(), "line": use.line, "text": use.text})
    return found


def library_screens(data: dict) -> list[dict]:
    """Each screen's last shot with its assets in place."""
    return library.screens(load(_folder(data)))


def library_rename_plan(data: dict) -> dict:
    """What renaming an asset would change, without changing anything."""
    return library.rename_plan(load(_folder(data)), str(data.get("name", "")), str(data.get("to", "")))


def library_delete(data: dict) -> dict:
    """Delete an asset's files."""
    return library.delete(load(_folder(data)), str(data.get("name", "")))


def library_rename(data: dict) -> dict:
    """Rename an asset and every line naming it, all at once."""
    return library.rename(load(_folder(data)), str(data.get("name", "")), str(data.get("to", "")))


def results_days(data: dict) -> list[dict]:
    """The Results page's day list: days with a run report, newest first, with their lead gain."""
    folder = _folder(data)
    return results.days(load(folder))


def results_day(data: dict) -> dict:
    """One day of the Results page (today when no day is given)."""
    folder = _folder(data)
    day = str(data.get("day") or datetime.now().strftime("%Y-%m-%d"))
    return results.day(load(folder), day)
