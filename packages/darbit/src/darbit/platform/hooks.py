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


def start(on_event: Callable[[str, str, int, int, int], None]) -> Callable[[], None]:
    """Start the hooks; on_event(kind, key, x, y, time_ns) is called from the hook thread's queue reader.
    Returns a function that removes the hooks."""
    raise NotImplementedError("TODO(T15)")
