"""Staying awake, the state of keys, and the processes darbit starts, through the system's System piece."""

from pathlib import Path

from . import backend


def keep_awake() -> None:
    """Stop the PC from sleeping or turning the screen off until the script ends."""
    try:
        backend.system().keep_awake()
    except backend.NotSupported:
        pass


def keys_down(codes: tuple[int, ...]) -> bool:
    """Whether every one of these key codes is held down right now."""
    return backend.system().keys_down(codes)


def screen_usable() -> bool:
    """Whether screen grabs and input reach the person's desktop: False while it's locked."""
    try:
        return backend.system().screen_usable()
    except backend.NotSupported:
        return True


def process_alive(pid: int) -> bool:
    return backend.system().process_alive(pid)


def end_process_tree(pid: int) -> None:
    """End a process and every process it started."""
    backend.system().end_process_tree(pid)


def site_packages(venv: Path) -> Path:
    """Where a virtual environment keeps its installed packages."""
    return backend.system().site_packages(venv)
