"""Staying awake, the state of keys, the processes darbit starts, taskbars that hide themselves and the tray's
hidden-icons flyout, through the system's System piece."""

import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

from . import backend


def no_window() -> int:
    """Popen's creationflags for a process of darbit's own (the service, a bot, the input worker) that must not open
    a console window. On Windows: CREATE_NO_WINDOW, a console that's never shown (never with DETACHED_PROCESS, which
    turns it off, so a venv's python.exe opened a window for the real one)."""
    if sys.platform == "win32":
        return subprocess.CREATE_NO_WINDOW
    return 0


def start_on_its_own(command: list[str], **popen) -> subprocess.Popen:
    """Start a process that outlives whatever started this one, such as the service. On Windows a terminal or an
    editor can keep its processes in a job and end them all when it closes: this one leaves that job where the job
    allows it (otherwise Windows refuses with error 5, and it starts in the job like any other)."""
    if sys.platform != "win32":
        return subprocess.Popen(command, start_new_session=True, **popen)
    try:
        return subprocess.Popen(command, creationflags=no_window() | subprocess.CREATE_BREAKAWAY_FROM_JOB, **popen)
    except PermissionError:
        return subprocess.Popen(command, creationflags=no_window(), **popen)


def keep_awake() -> None:
    """Stop the PC from sleeping or turning the screen off until the script ends."""
    try:
        backend.system().keep_awake()
    except backend.NotSupported:
        pass


def screen_usable() -> bool:
    """Whether screen grabs and input reach the person's desktop: False while it's locked."""
    try:
        return backend.system().screen_usable()
    except backend.NotSupported:
        return True


def on_battery() -> bool:
    """Whether the PC runs on its battery now; False when plugged in, without a battery, or where it can't be told."""
    try:
        return backend.system().on_battery()
    except backend.NotSupported:
        return False


@dataclass
class HiddenTaskbar:
    """A taskbar that hides itself, on a screen's `edge` (top, bottom, left, right), `size` pixels thick when shown."""

    edge: str
    size: int


def hidden_taskbars(left: int, top: int, right: int, bottom: int) -> list[HiddenTaskbar]:
    """The taskbars set to hide themselves on the screen at these pixels; none where there are none or it can't be
    told. The screen's work area leaves them out, though they slide out over its edge."""
    try:
        found = backend.system().hidden_taskbars(left, top, right, bottom)
    except backend.NotSupported:
        return []
    return [HiddenTaskbar(edge, size) for edge, size in found]


def tray_flyout() -> tuple[int, int, int, int] | None:
    """The taskbar's hidden-icons flyout while it's open, as (left, top, right, bottom) in pixels; None while it's
    closed or where there's none."""
    try:
        return backend.system().tray_flyout()
    except backend.NotSupported:
        return None


def process_alive(pid: int) -> bool:
    return backend.system().process_alive(pid)


def end_process_tree(pid: int) -> None:
    """End a process and every process it started."""
    backend.system().end_process_tree(pid)


def site_packages(venv: Path) -> Path:
    """Where a virtual environment keeps its installed packages."""
    return backend.system().site_packages(venv)


def name_app(app_id: str) -> None:
    """Give this process its own app id, so the taskbar shows its window's icon; nothing where there's no such id."""
    try:
        backend.system().name_app(app_id)
    except backend.NotSupported:
        pass


def add_shortcut(name: str, target: Path, arguments: str, icon: Path) -> list[Path]:
    """A shortcut to `target arguments` with this icon in the Start menu and on the desktop; returns the ones made."""
    return backend.system().add_shortcut(name, target, arguments, icon)
