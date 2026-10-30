"""The platform pieces: each forwards to the system's own version, and a system without one says so clearly."""

import pytest

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
