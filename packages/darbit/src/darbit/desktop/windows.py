"""pywebview windows with the Win32 styles each kind needs. See docs/tasks/T06-desktop-windows.md."""

from __future__ import annotations

from typing import Literal

Kind = Literal["normal", "overlay", "bar", "clickthrough"]

WS_EX_TOPMOST = 0x00000008
WS_EX_TRANSPARENT = 0x00000020
WS_EX_TOOLWINDOW = 0x00000080
WS_EX_LAYERED = 0x00080000
WS_EX_NOACTIVATE = 0x08000000


def styles(kind: Kind) -> int:
    """The extended window styles for a kind (a pure function, so it can be tested)."""
    raise NotImplementedError(
        "TODO(T06): bar = topmost | toolwindow | noactivate; clickthrough adds layered | transparent; overlay = topmost"
    )


class Window:
    """An open window. `wait()` blocks until it closes."""

    def close(self) -> None:
        raise NotImplementedError("TODO(T06)")

    def wait(self) -> None:
        raise NotImplementedError("TODO(T06)")


def open_window(app: str, kind: Kind = "normal", monitor: int | None = None, query: dict | None = None) -> Window:
    """Open packages/ui/src/apps/<app> as a desktop window. pywebview is imported here, not at the top."""
    raise NotImplementedError("TODO(T06)")
