"""A system for tests on machines darbit has no pieces for yet: every platform piece in one module.

conftest.py puts it in place off Windows. Screen, input, windows, the listener and hotkeys do nothing (tests that
need them bring their own fakes); processes are real, so the Studio's run tests can start and stop bots.
"""

import os
import signal
import sys
from pathlib import Path

import numpy as np

from darbit.core.geometry import Region

DESKTOP = Region(0, 0, 1920, 1080)

# ---- screen


def enable_dpi_awareness() -> None:
    return None


def desktop() -> Region:
    return DESKTOP


def monitors() -> list[Region]:
    return [DESKTOP]


def grab(region: Region | None = None) -> tuple[np.ndarray, Region]:
    area = region or DESKTOP
    return np.zeros((area.h, area.w, 3), dtype=np.uint8), area


def scale_at(x: int, y: int) -> float:
    return 1.0


# ---- input: nothing is sent


def position() -> tuple[int, int]:
    return (0, 0)


def input_desktop() -> tuple[int, int, int, int]:
    return (DESKTOP.x, DESKTOP.y, DESKTOP.w, DESKTOP.h)


def _nothing(*args: object, **kwargs: object) -> None:
    return None


move = move_by = mouse_down = mouse_up = click = drag = scroll = _nothing
key_down = key_up = tap = write = key_now = button_now = nudge = place = wheel_now = _nothing
release_all = let_go_of_everything = _nothing

# ---- windows: none


def windows() -> list:
    return []


def matching(name: str, loose: bool = False) -> list:
    return []


def in_front(handle: int) -> bool:
    return False


def bring_to_front(handle: int) -> bool:
    return False


def region(handle: int) -> Region:
    return DESKTOP


def close(name: str, wait: float = 5.0) -> bool:
    return False


# ---- listener and hotkeys: no real input


def start(on_event: object, moves: bool = False) -> object:
    return _nothing


def watch_mouse(on_move: object) -> object:
    return _nothing


def health(restart: bool = False) -> dict:
    return {"late": 0, "most_late": 0.0, "missed": 0}


def register(keys: dict, handlers: dict) -> object:
    return None


# ---- system: real processes


def keep_awake() -> None:
    return None


def allow_sleep() -> None:
    return None


def keys_down(codes: tuple[int, ...]) -> bool:
    return False


def process_alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return not _zombie(pid)


def _zombie(pid: int) -> bool:
    try:
        return Path(f"/proc/{pid}/stat").read_text().split(")")[-1].split()[0] == "Z"
    except OSError:
        return False


def end_process_tree(pid: int) -> None:
    for child in _children(pid):
        end_process_tree(child)
    try:
        os.kill(pid, signal.SIGKILL)
    except ProcessLookupError:
        pass


def _children(pid: int) -> list[int]:
    found = []
    for tasks in Path(f"/proc/{pid}/task").glob("*/children"):
        try:
            found.extend(int(child) for child in tasks.read_text().split())
        except OSError:
            continue
    return found


def site_packages(venv: Path) -> Path:
    version = f"python{sys.version_info.major}.{sys.version_info.minor}"
    return venv / "lib" / version / "site-packages"
