"""Real keyboard and mouse input for the recorder (T15) and the Studio's run pill (#130), through Raw Input.

Raw Input arrives as messages on a hidden window after Windows has handled the input, so nothing waits for
darbit: unlike low-level hooks, a busy Python can never make the mouse or the game's keys lag. Input that a
program sends (SendInput, which is how darbit clicks and types) has no device, so it's left out: a bot moving
the mouse never looks like the person moving it. One listener thread serves every subscriber in the process.
"""

import ctypes
import threading
import time
from collections.abc import Callable
from ctypes import wintypes

WM_INPUT = 0x00FF
WM_QUIT = 0x0012
RID_INPUT = 0x10000003
RIM_TYPEMOUSE = 0
RIM_TYPEKEYBOARD = 1
RIDEV_INPUTSINK = 0x00000100  # get input even while another window (the game) is in front
RIDEV_REMOVE = 0x00000001
HWND_MESSAGE = -3
RI_KEY_BREAK = 0x01  # the key went up
BUTTON_FLAGS = (
    (0x0001, "mouse_down", 0),
    (0x0002, "mouse_up", 0),
    (0x0004, "mouse_down", 1),
    (0x0008, "mouse_up", 1),
    (0x0010, "mouse_down", 2),
    (0x0020, "mouse_up", 2),
)
WHEEL = 0x0400
MOUSE_MOVE_ABSOLUTE = 0x0001  # usFlags: a tablet or remote desktop, not counts

OnEvent = Callable[[str, int, int, int, int], None]  # kind, code, x, y, time_ns


class RAWINPUTHEADER(ctypes.Structure):
    _fields_ = [
        ("dwType", wintypes.DWORD),
        ("dwSize", wintypes.DWORD),
        ("hDevice", wintypes.HANDLE),
        ("wParam", wintypes.WPARAM),
    ]


class RAWMOUSE(ctypes.Structure):
    _fields_ = [
        ("usFlags", wintypes.USHORT),
        ("_padding", wintypes.USHORT),
        ("usButtonFlags", wintypes.USHORT),
        ("usButtonData", wintypes.USHORT),
        ("ulRawButtons", wintypes.ULONG),
        ("lLastX", wintypes.LONG),
        ("lLastY", wintypes.LONG),
        ("ulExtraInformation", wintypes.ULONG),
    ]


class RAWKEYBOARD(ctypes.Structure):
    _fields_ = [
        ("MakeCode", wintypes.USHORT),
        ("Flags", wintypes.USHORT),
        ("Reserved", wintypes.USHORT),
        ("VKey", wintypes.USHORT),
        ("Message", wintypes.UINT),
        ("ExtraInformation", wintypes.ULONG),
    ]


class _DATA(ctypes.Union):
    _fields_ = [("mouse", RAWMOUSE), ("keyboard", RAWKEYBOARD)]


class RAWINPUT(ctypes.Structure):
    _fields_ = [("header", RAWINPUTHEADER), ("data", _DATA)]


class RAWINPUTDEVICE(ctypes.Structure):
    _fields_ = [
        ("usUsagePage", wintypes.USHORT),
        ("usUsage", wintypes.USHORT),
        ("dwFlags", wintypes.DWORD),
        ("hwndTarget", wintypes.HWND),
    ]


WNDPROC = ctypes.WINFUNCTYPE(ctypes.c_ssize_t, wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM)


class WNDCLASSW(ctypes.Structure):
    _fields_ = [
        ("style", wintypes.UINT),
        ("lpfnWndProc", WNDPROC),
        ("cbClsExtra", ctypes.c_int),
        ("cbWndExtra", ctypes.c_int),
        ("hInstance", wintypes.HINSTANCE),
        ("hIcon", wintypes.HICON),
        ("hCursor", wintypes.HANDLE),
        ("hbrBackground", wintypes.HBRUSH),
        ("lpszMenuName", wintypes.LPCWSTR),
        ("lpszClassName", wintypes.LPCWSTR),
    ]


def is_real(device: int | None) -> bool:
    """Whether raw input came from a keyboard or mouse; sent input (SendInput) has no device."""
    return bool(device)


def events_of(raw: RAWINPUT, cursor: tuple[int, int]) -> list[tuple[str, int, int, int]]:
    """What one raw input message means: (kind, code, x, y) for each key or button change, and mouse moves.

    Kinds: key_down, key_up (code: the virtual-key), mouse_down, mouse_up (code: 0 left, 1 right, 2 middle),
    wheel (code: notches), mouse_move, and mouse_delta (x, y: how far the mouse itself moved, in counts, even when a
    game holds the cursor still). Sent input gives nothing."""
    found: list[tuple[str, int, int, int]] = []
    if not is_real(raw.header.hDevice):
        return found
    x, y = cursor
    if raw.header.dwType == RIM_TYPEKEYBOARD:
        keyboard = raw.data.keyboard
        kind = "key_up" if keyboard.Flags & RI_KEY_BREAK else "key_down"
        found.append((kind, keyboard.VKey, 0, 0))
    elif raw.header.dwType == RIM_TYPEMOUSE:
        mouse = raw.data.mouse
        if mouse.lLastX or mouse.lLastY:
            found.append(("mouse_move", 0, x, y))
            if not mouse.usFlags & MOUSE_MOVE_ABSOLUTE:
                found.append(("mouse_delta", 0, mouse.lLastX, mouse.lLastY))
        for flag, kind, button in BUTTON_FLAGS:
            if mouse.usButtonFlags & flag:
                found.append((kind, button, x, y))
        if mouse.usButtonFlags & WHEEL:
            notches = ctypes.c_short(mouse.usButtonData).value // 120
            found.append(("wheel", notches, x, y))
    return found


class _Listener:
    """The one hidden window and thread that receive raw input for the whole process."""

    def __init__(self) -> None:
        self.subscribers: list[OnEvent] = []
        self.lock = threading.Lock()
        self.thread_id = 0
        self.ready = threading.Event()
        self.procedure = WNDPROC(self._window_procedure)  # kept alive while the window lives

    def add(self, on_event: OnEvent) -> None:
        with self.lock:
            self.subscribers.append(on_event)
            starting = len(self.subscribers) == 1
        if starting:
            self.ready.clear()
            threading.Thread(target=self._loop, name="darbit-raw-input", daemon=True).start()
            self.ready.wait(2)

    def remove(self, on_event: OnEvent) -> None:
        with self.lock:
            if on_event in self.subscribers:
                self.subscribers.remove(on_event)
            stopping = not self.subscribers
        if stopping and self.thread_id:
            ctypes.windll.user32.PostThreadMessageW(self.thread_id, WM_QUIT, 0, 0)

    def _window_procedure(self, hwnd: int, message: int, wparam: int, lparam: int) -> int:
        user32 = ctypes.windll.user32
        if message == WM_INPUT:
            self._input(lparam)
        return user32.DefWindowProcW(hwnd, message, wparam, lparam)

    def _input(self, handle: int) -> None:
        user32 = ctypes.windll.user32
        raw = RAWINPUT()
        size = wintypes.UINT(ctypes.sizeof(raw))
        got = user32.GetRawInputData(
            wintypes.HANDLE(handle), RID_INPUT, ctypes.byref(raw), ctypes.byref(size), ctypes.sizeof(RAWINPUTHEADER)
        )
        if got in (0, 0xFFFFFFFF):
            return
        # where the mouse was when this input happened, not now: by the time it's handled the mouse may have moved on
        position = user32.GetMessagePos()
        point = wintypes.POINT(ctypes.c_short(position & 0xFFFF).value, ctypes.c_short((position >> 16) & 0xFFFF).value)
        now = time.perf_counter_ns()
        with self.lock:
            subscribers = list(self.subscribers)
        for kind, code, x, y in events_of(raw, (point.x, point.y)):
            for on_event in subscribers:
                try:
                    on_event(kind, code, x, y, now)
                except Exception:  # noqa: BLE001, S110 - one broken listener must not stop the others
                    pass

    def _loop(self) -> None:
        user32 = ctypes.windll.user32
        kernel32 = ctypes.windll.kernel32
        user32.DefWindowProcW.argtypes = [wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM]
        user32.DefWindowProcW.restype = ctypes.c_ssize_t
        user32.CreateWindowExW.restype = wintypes.HWND
        user32.GetRawInputData.argtypes = [
            wintypes.HANDLE,
            wintypes.UINT,
            ctypes.c_void_p,
            ctypes.POINTER(wintypes.UINT),
            wintypes.UINT,
        ]
        self.thread_id = kernel32.GetCurrentThreadId()
        instance = kernel32.GetModuleHandleW(None)
        name = f"darbit-raw-input-{self.thread_id}"
        window_class = WNDCLASSW()
        window_class.lpfnWndProc = self.procedure
        window_class.hInstance = instance
        window_class.lpszClassName = name
        user32.RegisterClassW(ctypes.byref(window_class))
        hwnd = user32.CreateWindowExW(0, name, name, 0, 0, 0, 0, 0, wintypes.HWND(HWND_MESSAGE), None, instance, None)
        devices = (RAWINPUTDEVICE * 2)(
            RAWINPUTDEVICE(1, 2, RIDEV_INPUTSINK, hwnd), RAWINPUTDEVICE(1, 6, RIDEV_INPUTSINK, hwnd)
        )
        user32.RegisterRawInputDevices(devices, 2, ctypes.sizeof(RAWINPUTDEVICE))
        self.ready.set()
        message = wintypes.MSG()
        while user32.GetMessageW(ctypes.byref(message), None, 0, 0) > 0:
            user32.TranslateMessage(ctypes.byref(message))
            user32.DispatchMessageW(ctypes.byref(message))
        gone = (RAWINPUTDEVICE * 2)(RAWINPUTDEVICE(1, 2, RIDEV_REMOVE, None), RAWINPUTDEVICE(1, 6, RIDEV_REMOVE, None))
        user32.RegisterRawInputDevices(gone, 2, ctypes.sizeof(RAWINPUTDEVICE))
        user32.DestroyWindow(hwnd)
        user32.UnregisterClassW(name, instance)
        self.thread_id = 0


_listener = _Listener()


def start(on_event: OnEvent) -> Callable[[], None]:
    """Get every real key and mouse button change: `on_event(kind, code, x, y, time_ns)`. Returns a function
    that stops it. Mouse moves are left out here; the run pill uses `watch_mouse`."""

    def without_moves(kind: str, code: int, x: int, y: int, time_ns: int) -> None:
        if kind != "mouse_move":
            on_event(kind, code, x, y, time_ns)

    _listener.add(without_moves)

    def stop() -> None:
        _listener.remove(without_moves)

    return stop


def watch_mouse(on_move: Callable[[int, int], None]) -> Callable[[], None]:
    """Call on_move(x, y) for every real mouse move, in screen pixels. Returns a function that stops it."""

    def moves(kind: str, code: int, x: int, y: int, time_ns: int) -> None:
        if kind == "mouse_move":
            on_move(x, y)

    _listener.add(moves)

    def stop() -> None:
        _listener.remove(moves)

    return stop
