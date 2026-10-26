"""Finding, focusing and closing top-level windows and their apps.

An app is named by its window title ("Roblox") or by its program file
("chrome.exe", or a full path to it).
"""

import ctypes
import ntpath
import time
from ctypes import wintypes
from dataclasses import dataclass

from ..core.geometry import Region
from . import input as device
from .keys import Key, Keys

_user32 = ctypes.WinDLL("user32", use_last_error=True)
_kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
_EnumWindowsProc = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
_user32.EnumWindows.argtypes = (_EnumWindowsProc, wintypes.LPARAM)
_user32.GetWindowTextLengthW.argtypes = (wintypes.HWND,)
_user32.GetWindowTextW.argtypes = (wintypes.HWND, wintypes.LPWSTR, ctypes.c_int)
_user32.IsWindowVisible.argtypes = (wintypes.HWND,)
_user32.IsIconic.argtypes = (wintypes.HWND,)
_user32.ShowWindow.argtypes = (wintypes.HWND, ctypes.c_int)
_user32.SetForegroundWindow.argtypes = (wintypes.HWND,)
_user32.GetForegroundWindow.restype = wintypes.HWND
_user32.GetClientRect.argtypes = (wintypes.HWND, ctypes.POINTER(wintypes.RECT))
_user32.ClientToScreen.argtypes = (wintypes.HWND, ctypes.POINTER(wintypes.POINT))
_user32.GetWindowThreadProcessId.argtypes = (wintypes.HWND, ctypes.POINTER(wintypes.DWORD))
_user32.PostMessageW.argtypes = (wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM)
_kernel32.OpenProcess.restype = wintypes.HANDLE
_kernel32.OpenProcess.argtypes = (wintypes.DWORD, wintypes.BOOL, wintypes.DWORD)
_kernel32.QueryFullProcessImageNameW.argtypes = (
    wintypes.HANDLE,
    wintypes.DWORD,
    wintypes.LPWSTR,
    ctypes.POINTER(wintypes.DWORD),
)
_kernel32.CloseHandle.argtypes = (wintypes.HANDLE,)
_kernel32.TerminateProcess.argtypes = (wintypes.HANDLE, wintypes.UINT)

_WM_CLOSE = 0x0010
_SW_RESTORE = 9
_QUERY = 0x1000
_TERMINATE = 0x0001
# An unused virtual key; pressing it while Alt is down lets a background program bring a window to the front.
_MASK = Key("mask", 0x00, 0xE8)


@dataclass(frozen=True)
class Window:
    handle: int
    title: str
    exe: str
    pid: int


def _title(hwnd: int) -> str:
    length = _user32.GetWindowTextLengthW(hwnd)
    buffer = ctypes.create_unicode_buffer(length + 1)
    _user32.GetWindowTextW(hwnd, buffer, length + 1)
    return buffer.value


def _process(hwnd: int) -> tuple[str, int]:
    pid = wintypes.DWORD()
    _user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
    handle = _kernel32.OpenProcess(_QUERY, False, pid.value)
    if not handle:
        return "", pid.value
    try:
        size = wintypes.DWORD(32768)
        path = ctypes.create_unicode_buffer(size.value)
        if not _kernel32.QueryFullProcessImageNameW(handle, 0, path, ctypes.byref(size)):
            return "", pid.value
        return ntpath.basename(path.value), pid.value
    finally:
        _kernel32.CloseHandle(handle)


def windows() -> list[Window]:
    """Every visible top-level window with a title, front to back."""
    handles: list[int] = []

    def add(hwnd: int, _lparam: int) -> bool:
        handles.append(hwnd)
        return True

    _user32.EnumWindows(_EnumWindowsProc(add), 0)
    found = []
    for hwnd in handles:
        if not _user32.IsWindowVisible(hwnd):
            continue
        title = _title(hwnd)
        if not title:
            continue
        exe, pid = _process(hwnd)
        found.append(Window(hwnd, title, exe, pid))
    return found


def _is_program(name: str) -> bool:
    return name.lower().endswith(".exe") or "\\" in name or "/" in name


def matching(name: str, loose: bool = False) -> list[Window]:
    """Windows of an app: by program file, or by exact title. `loose` also allows titles containing `name`."""
    every = windows()
    if _is_program(name):
        exe = ntpath.basename(name.replace("/", "\\")).lower()
        return [w for w in every if w.exe.lower() == exe]
    exact = [w for w in every if w.title == name]
    if exact or not loose:
        return exact
    return [w for w in every if name.lower() in w.title.lower()]


def in_front(handle: int) -> bool:
    return _user32.GetForegroundWindow() == handle


def _wait_front(handle: int, within: float) -> bool:
    deadline = time.monotonic() + within
    while not in_front(handle):
        if time.monotonic() >= deadline:
            return False
        time.sleep(0.01)
    return True


def bring_to_front(handle: int) -> bool:
    if _user32.IsIconic(handle):
        _user32.ShowWindow(handle, _SW_RESTORE)
    _user32.SetForegroundWindow(handle)
    if _wait_front(handle, 0.1):
        return True
    device.key_down(Keys.ALT)
    try:
        device.tap(_MASK)
        _user32.SetForegroundWindow(handle)
    finally:
        device.key_up(Keys.ALT)
    return _wait_front(handle, 0.5)


def region(handle: int) -> Region:
    """A window's content area (no title bar or borders) on screen."""
    rect, corner = wintypes.RECT(), wintypes.POINT(0, 0)
    _user32.GetClientRect(handle, ctypes.byref(rect))
    _user32.ClientToScreen(handle, ctypes.byref(corner))
    return Region(corner.x, corner.y, rect.right, rect.bottom)


def close(name: str, wait: float = 5.0) -> bool:
    """Close an app's windows politely; end its process if they're still there after `wait` seconds."""
    found = matching(name)
    for window in found:
        _user32.PostMessageW(window.handle, _WM_CLOSE, 0, 0)
    deadline = time.monotonic() + wait
    while found and time.monotonic() < deadline:
        handles = {w.handle for w in windows()}
        if not any(w.handle in handles for w in found):
            return True
        time.sleep(0.1)
    for pid in {w.pid for w in found if w.handle in {x.handle for x in windows()}}:
        process = _kernel32.OpenProcess(_TERMINATE, False, pid)
        if process:
            _kernel32.TerminateProcess(process, 1)
            _kernel32.CloseHandle(process)
    return bool(found)
