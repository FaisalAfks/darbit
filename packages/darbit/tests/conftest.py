"""Tests run on any system: off Windows, the platform pieces come from fake_system.py, and the tests of Windows'
own pieces (they load its system libraries) are left out. Windows CI runs everything."""

import sys
import types

import fake_system

from darbit.platform import backend

PIECES = ("screen", "input", "windows", "listener", "hotkeys", "system")
WINDOWS_ONLY = ["test_hooks.py", "test_input.py", "test_observe.py", "test_windows.py"]

collect_ignore = []


def _use_fake_system() -> None:
    """Make fake_system this system's version of every piece; input gets its own desktop()."""
    names = {}
    for piece in PIECES:
        name = f"fake_system_{piece}"
        module = types.ModuleType(name)
        module.__dict__.update(vars(fake_system))
        if piece == "input":
            module.desktop = fake_system.input_desktop
        sys.modules[name] = module
        names[piece] = name
    backend.MODULES[sys.platform] = names


if sys.platform != "win32":
    collect_ignore = WINDOWS_ONLY
    _use_fake_system()
