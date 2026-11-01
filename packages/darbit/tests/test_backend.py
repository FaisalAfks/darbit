"""The platform pieces: each forwards to the system's own version, and a system without one says so clearly."""

from pathlib import Path

import pytest

import darbit
from darbit.platform import backend, input, screen, system


@pytest.fixture
def elsewhere(monkeypatch):
    """darbit on a system it has no pieces for yet."""
    monkeypatch.setattr(backend.sys, "platform", "plan9")


def test_another_system_is_told_plainly(elsewhere):
    with pytest.raises(backend.NotSupported, match="Windows for now"):
        screen.grab()
    with pytest.raises(backend.NotSupported):
        input.position()


def test_what_runs_on_import_or_exit_never_fails_elsewhere(elsewhere):
    screen.enable_dpi_awareness()  # darbit/__init__.py calls it on import
    system.keep_awake()  # the first darbit call does
    input.release_all()  # at exit


def test_windows_has_every_piece():
    for piece in ("screen", "input", "windows", "listener", "hotkeys", "system"):
        assert piece in backend.MODULES["win32"]


def test_windows_modules_import_what_they_use_of_ctypes():
    """`ctypes.wintypes` works only once something has imported it: a module that leans on another having done so
    breaks when the pieces load lazily (scale_at said 1.0 on a 150% screen that way)."""
    folder = Path(darbit.__file__).parent / "platform" / "win32"
    for module in folder.glob("*.py"):
        text = module.read_text(encoding="utf-8")
        assert "ctypes.wintypes." not in text, f"{module.name}: use `from ctypes import wintypes`"
        if "wintypes." in text:
            assert "from ctypes import wintypes" in text, f"{module.name} uses wintypes without importing it"
