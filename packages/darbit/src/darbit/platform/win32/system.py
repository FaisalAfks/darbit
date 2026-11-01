"""Windows' side of the system piece: keeping the PC awake, the state of keys, and the processes darbit starts."""

import atexit
import ctypes
import subprocess
from pathlib import Path

_ES_CONTINUOUS, _ES_SYSTEM_REQUIRED, _ES_DISPLAY_REQUIRED = 0x80000000, 0x00000001, 0x00000002
PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
DESKTOP_READOBJECTS = 0x0001
UOI_NAME = 2
STILL_ACTIVE = 259  # GetExitCodeProcess's code for a process that hasn't ended


def keep_awake() -> None:
    """Stop Windows from sleeping or turning the screen off until the script ends."""
    try:
        ctypes.windll.kernel32.SetThreadExecutionState(_ES_CONTINUOUS | _ES_SYSTEM_REQUIRED | _ES_DISPLAY_REQUIRED)
        atexit.register(allow_sleep)
    except (AttributeError, OSError):
        pass


def allow_sleep() -> None:
    """Let Windows sleep again, as it would after the script ends."""
    ctypes.windll.kernel32.SetThreadExecutionState(_ES_CONTINUOUS)


def keys_down(codes: tuple[int, ...]) -> bool:
    """Whether every one of these virtual-key codes is held down right now."""
    get_state = ctypes.windll.user32.GetAsyncKeyState
    get_state.argtypes = (ctypes.c_int,)
    get_state.restype = ctypes.c_short
    for code in codes:
        if not get_state(code) & 0x8000:
            return False
    return True


def screen_usable() -> bool:
    """False while Windows is locked, or shows its sign-in or a UAC prompt: the desktop taking input then isn't
    the person's ("Default"), and screen grabs and input don't reach the game."""
    from ctypes import wintypes

    user32 = ctypes.windll.user32
    user32.OpenInputDesktop.restype = wintypes.HANDLE
    user32.OpenInputDesktop.argtypes = (wintypes.DWORD, wintypes.BOOL, wintypes.DWORD)
    user32.GetUserObjectInformationW.argtypes = (
        wintypes.HANDLE,
        ctypes.c_int,
        ctypes.c_void_p,
        wintypes.DWORD,
        ctypes.POINTER(wintypes.DWORD),
    )
    user32.CloseDesktop.argtypes = (wintypes.HANDLE,)
    desktop = user32.OpenInputDesktop(0, False, DESKTOP_READOBJECTS)
    if not desktop:
        return False  # the secure desktop (locked, sign-in, UAC) can't be opened from here
    try:
        name = ctypes.create_unicode_buffer(64)
        needed = wintypes.DWORD()
        if not user32.GetUserObjectInformationW(desktop, UOI_NAME, name, ctypes.sizeof(name), ctypes.byref(needed)):
            return True
        return name.value.lower() == "default"
    finally:
        user32.CloseDesktop(desktop)


def process_alive(pid: int) -> bool:
    kernel32 = ctypes.windll.kernel32
    handle = kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid)
    if not handle:
        return False
    code = ctypes.c_ulong()
    try:
        kernel32.GetExitCodeProcess(handle, ctypes.byref(code))
    finally:
        kernel32.CloseHandle(handle)
    return code.value == STILL_ACTIVE


def end_process_tree(pid: int) -> None:
    """End a process and every process it started: a child (the bot under `uv run`) outlives its parent on Windows
    if only the parent is ended."""
    subprocess.run(["taskkill", "/PID", str(pid), "/T", "/F"], capture_output=True, check=False)


def site_packages(venv: Path) -> Path:
    """Where a virtual environment keeps its installed packages."""
    return venv / "Lib" / "site-packages"
