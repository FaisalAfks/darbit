"""pywebview windows with the Win32 styles each kind needs. See docs/tasks/T06-desktop-windows.md.

Every window loads a UI app from the local server (or the Vite dev server with DARBIT_UI_DEV=1) with the
server's port and token. pywebview runs on the main thread: `run()` starts it with the first window and
blocks; windows opened later (from the server, say) appear as they're made.
"""

import ctypes
import threading
from ctypes import wintypes
from pathlib import Path
from typing import Literal
from urllib.parse import urlencode

Kind = Literal["normal", "overlay", "bar", "clickthrough"]

WS_EX_TOPMOST = 0x00000008
WS_EX_TRANSPARENT = 0x00000020
WS_EX_TOOLWINDOW = 0x00000080
WS_EX_LAYERED = 0x00080000
WS_EX_NOACTIVATE = 0x08000000
GWL_EXSTYLE = -20

# the size a window of each kind opens at, in pixels (the page lays itself out inside)
SIZES = {
    "normal": (1280, 860),
    "bar": (460, 64),
    "overlay": (0, 0),
    "clickthrough": (0, 0),
}
TITLES = {"hub": "darbit Studio"}
BAR_MIN_SIZE = (120, 32)
BAR_BACKGROUND = "#0b0d12"  # a bar's window before its page draws, the Studio's own background
DWMWA_WINDOW_CORNER_PREFERENCE = 33
DWMWCP_ROUND = 2
ICON = Path(__file__).with_name("darbit.ico")  # darbit's logo (assets/logo.svg) at every size Windows asks for
APP_ID = "darbit.Studio"  # the taskbar groups darbit's windows under this, with darbit's icon, not Python's
WM_SETICON = 0x0080
ICON_SMALL, ICON_BIG = 0, 1
IMAGE_ICON = 1
LR_LOADFROMFILE = 0x00000010
SM_CXICON, SM_CXSMICON = 11, 49


def styles(kind: Kind) -> int:
    """The extended window styles for a kind (a pure function, so it can be tested)."""
    if kind == "bar":
        return WS_EX_TOPMOST | WS_EX_TOOLWINDOW | WS_EX_NOACTIVATE
    if kind == "clickthrough":
        return WS_EX_TOPMOST | WS_EX_TOOLWINDOW | WS_EX_NOACTIVATE | WS_EX_LAYERED | WS_EX_TRANSPARENT
    if kind == "overlay":
        return WS_EX_TOPMOST
    return 0


class Window:
    """An open window. `wait()` blocks until it closes."""

    def __init__(self, native: object, kind: Kind) -> None:
        self.native = native  # the pywebview window
        self.kind = kind
        self.closed = threading.Event()
        self.opened = threading.Event()  # set once the real window exists

    def close(self) -> None:
        self.native.destroy()

    def show(self) -> None:
        self.native.show()

    def hide(self) -> None:
        self.native.hide()

    def move(self, x: int, y: int) -> None:
        self.native.move(x, y)

    def wait(self) -> None:
        self.closed.wait()

    def handle(self) -> int:
        """The Win32 window handle (once `opened` is set)."""
        return self.native.native.Handle.ToInt64()


def page_url(app: str, query: dict | None = None) -> str:
    """Where a window loads its app from, with the server's port and token."""
    from ..server import serve
    from ..ui import app_url

    server = serve()
    values = {"port": server.port, "token": server.token}
    if query:
        values.update(query)
    return app_url(app, server.port) + "?" + urlencode(values)


def _add_styles(native: object, kind: Kind) -> None:
    """Set the kind's extended styles on the real window once it exists (bars never take focus, and get the
    rounded corners Windows 11 gives normal windows)."""
    extra = styles(kind)
    if not extra:
        return
    handle = native.native.Handle.ToInt64()  # the WinForms form pywebview made
    if kind == "bar":
        corner = ctypes.c_int(DWMWCP_ROUND)
        ctypes.windll.dwmapi.DwmSetWindowAttribute(
            ctypes.c_void_p(handle), DWMWA_WINDOW_CORNER_PREFERENCE, ctypes.byref(corner), ctypes.sizeof(corner)
        )
    user32 = ctypes.windll.user32
    current = user32.GetWindowLongPtrW(ctypes.c_void_p(handle), GWL_EXSTYLE)
    user32.SetWindowLongPtrW(ctypes.c_void_p(handle), GWL_EXSTYLE, current | extra)


def _set_icon(native: object) -> None:
    """Give the window darbit's icon, for its title bar, the taskbar and Alt+Tab."""
    handle = native.native.Handle.ToInt64()
    user32 = ctypes.windll.user32
    user32.LoadImageW.argtypes = (
        wintypes.HINSTANCE,
        wintypes.LPCWSTR,
        wintypes.UINT,
        ctypes.c_int,
        ctypes.c_int,
        wintypes.UINT,
    )
    user32.LoadImageW.restype = wintypes.HANDLE
    user32.SendMessageW.argtypes = (wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM)
    for which, metric in ((ICON_BIG, SM_CXICON), (ICON_SMALL, SM_CXSMICON)):
        size = user32.GetSystemMetrics(metric)
        icon = user32.LoadImageW(None, str(ICON), IMAGE_ICON, size, size, LR_LOADFROMFILE)
        if icon:
            user32.SendMessageW(ctypes.c_void_p(handle), WM_SETICON, which, icon)


def open_window(
    app: str, kind: Kind = "normal", monitor: int | None = None, query: dict | None = None, extra: dict | None = None
) -> Window:
    """Open packages/ui/src/apps/<app> as a desktop window. pywebview is imported here, not at the top.

    `extra` holds more pywebview options (a place, a size, a background colour) and wins over the defaults.
    """
    import webview

    width, height = SIZES[kind]
    options = {"width": width, "height": height}
    if extra:
        options.update(extra)
    if kind != "normal":
        options.update({"frameless": True, "on_top": True, "easy_drag": False, "focus": False, "transparent": True})
    if kind == "bar":
        options["easy_drag"] = True  # a bar is moved by dragging it anywhere
        # the page fills a bar's window: pywebview's transparency on Windows leaves the form's grey showing
        options["transparent"] = False
        options.setdefault("background_color", BAR_BACKGROUND)
        options.setdefault("min_size", BAR_MIN_SIZE)  # pywebview's own minimum (200 x 100) is taller than a bar
    if kind == "overlay":
        options["focus"] = True  # Capture's keys (Esc, Enter, arrows) need the keyboard
    if kind in ("overlay", "clickthrough"):
        options["fullscreen"] = True  # never easy_drag: a drag on the overlay draws a box, it mustn't move the window
    native = webview.create_window(TITLES.get(app, f"darbit {app}"), page_url(app, query), **options)
    window = Window(native, kind)
    native.events.closed += window.closed.set

    def shown() -> None:
        try:
            if kind == "normal":
                _set_icon(native)
            _add_styles(native, kind)
        except (AttributeError, OSError):
            pass  # without the styles the window still works; it may take focus when clicked
        window.opened.set()

    native.events.shown += shown
    return window


def run(debug: bool = False) -> None:
    """Start pywebview's loop on this (the main) thread; returns when the last window closes."""
    import webview

    try:
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(APP_ID)
    except (AttributeError, OSError):
        pass  # the taskbar then shows Python's icon; the windows still have darbit's
    webview.start(debug=debug)
