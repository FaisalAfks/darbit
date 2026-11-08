"""Tests run on any system: off Windows, the platform pieces come from fake_system.py, and the tests of Windows'
own pieces (they load its system libraries) are left out. Windows CI runs everything."""

import os
import sys
import tempfile
import types

# darbit's own folders (settings, the service's address, logs) in a folder of the test run's, for this process and
# every service or bot a test starts: a test never reads or writes the real ones
os.environ["DARBIT_HOME"] = tempfile.mkdtemp(prefix="darbit-tests-")
# no real input (mouse, keys, apps, screen grabs) in this process or what it starts: a call a test forgot to fake
# raises instead of touching the PC (platform/real.py). The live tests turn it back on (live/conftest.py)
os.environ["DARBIT_NO_REAL_INPUT"] = "1"

import fake_system
import pytest

from darbit.platform import backend

PIECES = ("screen", "input", "windows", "listener", "hotkeys", "system")
WINDOWS_ONLY = ["test_hooks.py", "test_input.py", "test_observe.py", "test_windows.py"]

collect_ignore = []


@pytest.fixture
def real_input(monkeypatch):
    """Real input back on for a test that fakes the system's own sending (win32's _send) instead."""
    monkeypatch.delenv("DARBIT_NO_REAL_INPUT", raising=False)


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
