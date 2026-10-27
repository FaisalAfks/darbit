"""Low-level keyboard and mouse hooks: the recorder (T15) and the Studio's run pill (#130).

WH_MOUSE_LL on its own thread with a message loop. The callback only hands the position on and returns
at once. Injected events (darbit's own input, sent with SendInput) are skipped, so a bot moving the mouse
never looks like the person moving it.
"""

import ctypes
import threading
from collections.abc import Callable
from ctypes import wintypes

WH_MOUSE_LL = 14
WM_MOUSEMOVE = 0x0200
WM_QUIT = 0x0012
LLMHF_INJECTED = 0x01
LLMHF_LOWER_IL_INJECTED = 0x02


class MSLLHOOKSTRUCT(ctypes.Structure):
    _fields_ = [
        ("pt", wintypes.POINT),
        ("mouseData", wintypes.DWORD),
        ("flags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ctypes.c_size_t),
    ]


HOOKPROC = ctypes.WINFUNCTYPE(ctypes.c_ssize_t, ctypes.c_int, wintypes.WPARAM, wintypes.LPARAM)


def is_real(flags: int) -> bool:
    """Whether a mouse event came from a person, not from SendInput (darbit's or any other program's)."""
    return not flags & (LLMHF_INJECTED | LLMHF_LOWER_IL_INJECTED)


def watch_mouse(on_move: Callable[[int, int], None]) -> Callable[[], None]:
    """Call on_move(x, y) for every real mouse move, in screen pixels. Returns a function that stops it."""
    user32 = ctypes.windll.user32
    user32.CallNextHookEx.argtypes = [wintypes.HHOOK, ctypes.c_int, wintypes.WPARAM, wintypes.LPARAM]
    user32.CallNextHookEx.restype = ctypes.c_ssize_t
    user32.SetWindowsHookExW.argtypes = [ctypes.c_int, HOOKPROC, wintypes.HINSTANCE, wintypes.DWORD]
    user32.SetWindowsHookExW.restype = wintypes.HHOOK
    started = threading.Event()
    thread_id = [0]

    def callback(code: int, kind: int, data: int) -> int:
        if code >= 0 and kind == WM_MOUSEMOVE:
            event = ctypes.cast(data, ctypes.POINTER(MSLLHOOKSTRUCT)).contents
            if is_real(event.flags):
                try:
                    on_move(event.pt.x, event.pt.y)
                except Exception:  # noqa: BLE001, S110 - a broken listener must never block the mouse
                    pass
        return user32.CallNextHookEx(None, code, kind, data)

    procedure = HOOKPROC(callback)  # kept alive by this closure for as long as the hook runs

    def loop() -> None:
        thread_id[0] = ctypes.windll.kernel32.GetCurrentThreadId()
        hook = user32.SetWindowsHookExW(WH_MOUSE_LL, procedure, None, 0)
        started.set()
        message = wintypes.MSG()
        while user32.GetMessageW(ctypes.byref(message), None, 0, 0) > 0:
            user32.TranslateMessage(ctypes.byref(message))
            user32.DispatchMessageW(ctypes.byref(message))
        if hook:
            user32.UnhookWindowsHookEx(hook)

    threading.Thread(target=loop, name="darbit-mouse-hook", daemon=True).start()
    started.wait(2)

    def stop() -> None:
        user32.PostThreadMessageW(thread_id[0], WM_QUIT, 0, 0)

    return stop


WH_KEYBOARD_LL = 13
LLKHF_INJECTED = 0x10
LLKHF_LOWER_IL_INJECTED = 0x02
KEY_MESSAGES = {0x0100: "key_down", 0x0104: "key_down", 0x0101: "key_up", 0x0105: "key_up"}
MOUSE_MESSAGES = {
    0x0201: ("mouse_down", "left"),
    0x0202: ("mouse_up", "left"),
    0x0204: ("mouse_down", "right"),
    0x0205: ("mouse_up", "right"),
    0x0207: ("mouse_down", "middle"),
    0x0208: ("mouse_up", "middle"),
    0x020A: ("wheel", ""),
}


class KBDLLHOOKSTRUCT(ctypes.Structure):
    _fields_ = [
        ("vkCode", wintypes.DWORD),
        ("scanCode", wintypes.DWORD),
        ("flags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ctypes.c_size_t),
    ]


def key_is_real(flags: int) -> bool:
    """Whether a key event came from the keyboard, not from SendInput."""
    return not flags & (LLKHF_INJECTED | LLKHF_LOWER_IL_INJECTED)


def start(on_event: Callable[[str, int, int, int, int], None]) -> Callable[[], None]:
    """Start the keyboard and mouse hooks for the recorder. `on_event(kind, code, x, y, time_ns)` gets every real
    key down/up (code: the virtual-key code) and mouse button and wheel event (code: 0 left, 1 right, 2 middle,
    or the wheel's notches). Returns a function that removes the hooks."""
    import time

    user32 = ctypes.windll.user32
    user32.CallNextHookEx.argtypes = [wintypes.HHOOK, ctypes.c_int, wintypes.WPARAM, wintypes.LPARAM]
    user32.CallNextHookEx.restype = ctypes.c_ssize_t
    user32.SetWindowsHookExW.argtypes = [ctypes.c_int, HOOKPROC, wintypes.HINSTANCE, wintypes.DWORD]
    user32.SetWindowsHookExW.restype = wintypes.HHOOK
    started = threading.Event()
    thread_id = [0]
    buttons = {"left": 0, "right": 1, "middle": 2}

    def keyboard(code: int, kind: int, data: int) -> int:
        if code >= 0 and kind in KEY_MESSAGES:
            event = ctypes.cast(data, ctypes.POINTER(KBDLLHOOKSTRUCT)).contents
            if key_is_real(event.flags):
                _safe(on_event, KEY_MESSAGES[kind], event.vkCode, 0, 0, time.perf_counter_ns())
        return user32.CallNextHookEx(None, code, kind, data)

    def mouse(code: int, kind: int, data: int) -> int:
        if code >= 0 and kind in MOUSE_MESSAGES:
            event = ctypes.cast(data, ctypes.POINTER(MSLLHOOKSTRUCT)).contents
            if is_real(event.flags):
                name, button = MOUSE_MESSAGES[kind]
                value = buttons.get(button, 0)
                if name == "wheel":
                    value = ctypes.c_short(event.mouseData >> 16).value // 120
                _safe(on_event, name, value, event.pt.x, event.pt.y, time.perf_counter_ns())
        return user32.CallNextHookEx(None, code, kind, data)

    keyboard_procedure = HOOKPROC(keyboard)  # kept alive by this closure while the hooks run
    mouse_procedure = HOOKPROC(mouse)

    def loop() -> None:
        thread_id[0] = ctypes.windll.kernel32.GetCurrentThreadId()
        hooks = [
            user32.SetWindowsHookExW(WH_KEYBOARD_LL, keyboard_procedure, None, 0),
            user32.SetWindowsHookExW(WH_MOUSE_LL, mouse_procedure, None, 0),
        ]
        started.set()
        message = wintypes.MSG()
        while user32.GetMessageW(ctypes.byref(message), None, 0, 0) > 0:
            user32.TranslateMessage(ctypes.byref(message))
            user32.DispatchMessageW(ctypes.byref(message))
        for hook in hooks:
            if hook:
                user32.UnhookWindowsHookEx(hook)

    threading.Thread(target=loop, name="darbit-record-hooks", daemon=True).start()
    started.wait(2)

    def stop() -> None:
        user32.PostThreadMessageW(thread_id[0], WM_QUIT, 0, 0)

    return stop


def _safe(on_event: Callable[[str, int, int, int, int], None], *values: object) -> None:
    try:
        on_event(*values)
    except Exception:  # noqa: BLE001, S110 - a broken listener must never block the keyboard or mouse
        pass
