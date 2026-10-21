"""Simple GUI automation for Windows.

    import darbit as d

    d.click("lobby/play")                  # True if clicked, False if not found in time
    if m := d.exists("run/enemies_left", 90):
        d.press("tab")
    d.press(*"54132")
"""
import atexit as _atexit

from .platform import screen as _screen

_screen.enable_dpi_awareness()

from .core.geometry import Location, Region
from .core.targets import Match, Target
from .errors import DarbitError, Interrupted, Stopped, TargetError, UnknownKey
from .platform import input as _input
from .platform import safety as _safety
from .platform.keys import Keys
from .platform.safety import no_interrupts
from .platform.screen import Screen
from .runtime import apps
from .runtime.actions import (
    click,
    double_click,
    drag,
    hold,
    hover,
    press,
    release,
    right_click,
    scroll,
    sleep,
    write,
)
from .runtime.find import check, exists, find_all, vanish, wait
from .runtime.log import log, screenshot
from .runtime.observe import Observer, observe, observers, stop_observing
from .settings import settings

__version__ = "0.1.0"


def stop_key(combo: str) -> None:
    """Change the stop hotkey, e.g. stop_key("ctrl+alt+q")."""
    settings.stop_key = combo
    _safety.arm()
    _safety.watch(combo)


_atexit.register(_input.release_all)

__all__ = [
    "DarbitError",
    "Interrupted",
    "Keys",
    "Location",
    "Match",
    "Observer",
    "Region",
    "Screen",
    "Stopped",
    "Target",
    "TargetError",
    "UnknownKey",
    "apps",
    "check",
    "click",
    "double_click",
    "drag",
    "exists",
    "find_all",
    "hold",
    "hover",
    "log",
    "no_interrupts",
    "observe",
    "observers",
    "press",
    "release",
    "right_click",
    "screenshot",
    "scroll",
    "settings",
    "sleep",
    "stop_key",
    "stop_observing",
    "vanish",
    "wait",
    "write",
]
