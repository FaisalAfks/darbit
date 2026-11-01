"""Simple GUI automation for Windows.

import darbit as d

d.click("lobby/play")                  # True if clicked, False if not found in time
if d.exists("run/enemies_left", 90):    # the Match, or None after 90 s
    d.press("tab")
d.press(*"54132")

game = d.App("Roblox").window           # a Region: game.exists(...), game.click(...)
play = d.Pattern("Lobby.Play").similar(0.85).offset(10, 0)
"""

import atexit as _atexit
import os as _os

# numpy's OpenBLAS commits a buffer per CPU thread when it loads, about 750 MB on a 24-thread PC, for matrix maths
# darbit never does (OpenCV matches on its own). Set before numpy loads; the processes darbit starts inherit it.
_os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")

from .platform import screen as _screen

_screen.enable_dpi_awareness()

from .core.geometry import Location
from .core.targets import Match, Pattern, Target
from .errors import DarbitError, Interrupted, Stopped, TargetError, UnknownKey
from .platform import input as _input
from .platform import safety as _safety
from .platform.keys import Keys
from .platform.safety import no_interrupts
from .runtime import apps
from .runtime.actions import (
    click,
    double_click,
    drag,
    hold,
    hover,
    mouse_down,
    mouse_up,
    move_by,
    press,
    release,
    right_click,
    scroll,
    sleep,
    write,
)
from .runtime.apps import App
from .runtime.find import check, exists, find, find_all, vanish, wait
from .runtime.log import log, screenshot
from .runtime.observe import Observer, observe, observers, stop_observing
from .runtime.region import Region, Screen, area, point
from .runtime.screens import Map, go
from .runtime.screens import default as screens
from .runtime.show import Record, next_up, plan, progress
from .runtime.state import State, Timer
from .runtime.steps import flow, step
from .runtime.tape import replay
from .settings import settings

next = next_up  # d.next("Weekly reset", when): shown in darbit Studio (decision 0011)
record = Record()  # d.record("event", ...) and d.record.gain("Gems", 120): the run report (decision 0013)

__version__ = "1.0.0.dev0"


def stop_key(combo: str) -> None:
    """Change the stop hotkey, e.g. stop_key("ctrl+alt+q")."""
    settings.stop_key = combo
    _safety.arm()
    _safety.watch(combo)


_atexit.register(_input.release_all)

from .project import manifest as _manifest

_project = _manifest.setup(settings, __version__)  # layer 2 of the settings: the bot's darbit.toml, if it has one

__all__ = [
    "App",
    "DarbitError",
    "Interrupted",
    "Keys",
    "Location",
    "Map",
    "Match",
    "Observer",
    "Pattern",
    "Region",
    "Screen",
    "State",
    "Stopped",
    "Target",
    "TargetError",
    "Timer",
    "UnknownKey",
    "apps",
    "area",
    "check",
    "click",
    "double_click",
    "drag",
    "exists",
    "find",
    "find_all",
    "flow",
    "go",
    "hold",
    "hover",
    "log",
    "mouse_down",
    "mouse_up",
    "move_by",
    "next",
    "no_interrupts",
    "observe",
    "observers",
    "plan",
    "point",
    "press",
    "progress",
    "record",
    "release",
    "replay",
    "right_click",
    "screens",
    "screenshot",
    "scroll",
    "settings",
    "sleep",
    "step",
    "stop_key",
    "stop_observing",
    "vanish",
    "wait",
    "write",
]
