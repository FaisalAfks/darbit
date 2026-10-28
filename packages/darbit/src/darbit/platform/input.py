"""Mouse and keyboard through SendInput, timed like SikuliX.

- The mouse glides to a spot (fast start, soft landing) and sends real move events
  all the way, so games like Roblox register the hover before the click.
- Keys carry both the scan code (the key's position) and the US virtual key, so
  games get them and the keyboard language doesn't matter.
- A short pause follows every press and release.
"""

import ctypes
import threading
import time
from ctypes import wintypes

from . import safety
from .keys import Key, Keys, key, names

_user32 = ctypes.WinDLL("user32", use_last_error=True)
_ULONG_PTR = ctypes.c_size_t


class _MOUSEINPUT(ctypes.Structure):
    _fields_ = [
        ("dx", wintypes.LONG),
        ("dy", wintypes.LONG),
        ("mouseData", wintypes.DWORD),
        ("dwFlags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", _ULONG_PTR),
    ]


class _KEYBDINPUT(ctypes.Structure):
    _fields_ = [
        ("wVk", wintypes.WORD),
        ("wScan", wintypes.WORD),
        ("dwFlags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", _ULONG_PTR),
    ]


class _HARDWAREINPUT(ctypes.Structure):
    _fields_ = [("uMsg", wintypes.DWORD), ("wParamL", wintypes.WORD), ("wParamH", wintypes.WORD)]


class _INPUTUNION(ctypes.Union):
    _fields_ = [("mi", _MOUSEINPUT), ("ki", _KEYBDINPUT), ("hi", _HARDWAREINPUT)]


class _INPUT(ctypes.Structure):
    _anonymous_ = ("u",)
    _fields_ = [("type", wintypes.DWORD), ("u", _INPUTUNION)]


_user32.SendInput.argtypes = (wintypes.UINT, ctypes.POINTER(_INPUT), ctypes.c_int)
_user32.SendInput.restype = wintypes.UINT
_user32.GetCursorPos.argtypes = (ctypes.POINTER(wintypes.POINT),)
_user32.GetSystemMetrics.argtypes = (ctypes.c_int,)

_MOUSE, _KEYBOARD = 0, 1
_MOVE, _WHEEL, _VIRTUALDESK, _ABSOLUTE = 0x0001, 0x0800, 0x4000, 0x8000
_HWHEEL = 0x01000
_KEYUP, _EXTENDED, _UNICODE = 0x0002, 0x0001, 0x0004
_BUTTONS = {"left": (0x0002, 0x0004), "right": (0x0008, 0x0010), "middle": (0x0020, 0x0040)}

STEP = 0.004  # pause between glide steps
EVENT_DELAY = 0.010  # after every press and release, like SikuliX
MOVE_BY_STEP = 0.01  # seconds between the small moves of a move_by
DRAG_DELAY = 0.3  # before pressing, after pressing, and before letting go in a drag, like SikuliX

_lock = threading.RLock()
_held_keys: dict[Key, None] = {}  # in the order they were pressed
_held_buttons: set[str] = set()


def _send(*events: _INPUT) -> None:
    array = (_INPUT * len(events))(*events)
    if _user32.SendInput(len(events), array, ctypes.sizeof(_INPUT)) != len(events):
        raise ctypes.WinError(ctypes.get_last_error())


def _desktop() -> tuple[int, int, int, int]:
    return tuple(_user32.GetSystemMetrics(i) for i in (76, 77, 78, 79))  # type: ignore[return-value]


def desktop() -> tuple[int, int, int, int]:
    """Every screen together: x, y, width, height."""
    return _desktop()


def _move_event(x: int, y: int) -> _INPUT:
    left, top, width, height = _desktop()
    event = _INPUT(type=_MOUSE)
    event.mi.dx = min(max(((x - left) * 65536 + width - 1) // width, 0), 65535)
    event.mi.dy = min(max(((y - top) * 65536 + height - 1) // height, 0), 65535)
    event.mi.dwFlags = _MOVE | _ABSOLUTE | _VIRTUALDESK
    return event


def _button_event(flag: int) -> _INPUT:
    event = _INPUT(type=_MOUSE)
    event.mi.dwFlags = flag
    return event


def _key_event(chosen: Key, up: bool) -> _INPUT:
    event = _INPUT(type=_KEYBOARD)
    event.ki.wVk = chosen.vk
    event.ki.wScan = chosen.scan
    event.ki.dwFlags = (_KEYUP if up else 0) | (_EXTENDED if chosen.extended else 0)
    return event


def _unicode_event(unit: int, up: bool) -> _INPUT:
    event = _INPUT(type=_KEYBOARD)
    event.ki.wScan = unit
    event.ki.dwFlags = _UNICODE | (_KEYUP if up else 0)
    return event


# ------------------------------------------------------------------------- mouse


def position() -> tuple[int, int]:
    point = wintypes.POINT()
    _user32.GetCursorPos(ctypes.byref(point))
    return point.x, point.y


def move(x: int, y: int, glide: float) -> None:
    """Glide the cursor to (x, y) in `glide` seconds (0 jumps)."""
    safety.check()
    start_x, start_y = position()
    if (start_x, start_y) == (x, y):
        return
    if glide > 0:
        started = time.perf_counter()
        last = (start_x, start_y)
        while True:
            t = (time.perf_counter() - started) / glide  # share of the glide done
            if t >= 1:
                break
            safety.check()
            eased = 1 - (1 - t) ** 4
            step = (round(start_x + (x - start_x) * eased), round(start_y + (y - start_y) * eased))
            if step != last:
                with _lock:
                    _send(_move_event(*step))
                last = step
            time.sleep(STEP)
    with _lock:
        _send(_move_event(x, y))


def move_by(dx: int, dy: int, seconds: float) -> None:
    """Move the mouse by (dx, dy) counts, spread over `seconds`. Games that lock the cursor (a camera) read these."""
    safety.check()
    parts = max(1, round(seconds / MOVE_BY_STEP))
    sent_x = 0
    sent_y = 0
    started = time.perf_counter()
    for part in range(1, parts + 1):
        safety.check()
        target_x = round(dx * part / parts)
        target_y = round(dy * part / parts)
        event = _INPUT(type=_MOUSE)
        event.mi.dx = target_x - sent_x
        event.mi.dy = target_y - sent_y
        event.mi.dwFlags = _MOVE  # relative: no _ABSOLUTE
        if event.mi.dx or event.mi.dy:
            with _lock:
                _send(event)
        sent_x = target_x
        sent_y = target_y
        due = started + seconds * part / parts
        left = due - time.perf_counter()
        if left > 0:
            time.sleep(left)


def mouse_down(button: str = "left") -> None:
    safety.check()
    with _lock:
        if button not in _held_buttons:
            _send(_button_event(_BUTTONS[button][0]))
            _held_buttons.add(button)
    time.sleep(EVENT_DELAY)


def mouse_up(button: str = "left") -> None:
    with _lock:
        if button in _held_buttons:
            _send(_button_event(_BUTTONS[button][1]))
            _held_buttons.discard(button)
    time.sleep(EVENT_DELAY)


def click(x: int, y: int, glide: float, button: str = "left", times: int = 1) -> None:
    move(x, y, glide)
    for _ in range(times):
        mouse_down(button)
        mouse_up(button)


def drag(from_x: int, from_y: int, to_x: int, to_y: int, glide: float) -> None:
    """Like SikuliX: glide, wait, press, wait, glide, wait, let go."""
    move(from_x, from_y, glide)
    safety.sleep(DRAG_DELAY)
    mouse_down()
    safety.sleep(DRAG_DELAY)
    move(to_x, to_y, glide)
    safety.sleep(DRAG_DELAY)
    mouse_up()


def scroll(notches: int) -> None:
    """Positive scrolls up, negative scrolls down."""
    safety.check()
    event = _INPUT(type=_MOUSE)
    event.mi.mouseData = ctypes.c_uint32(notches * 120).value
    event.mi.dwFlags = _WHEEL
    with _lock:
        _send(event)
    time.sleep(EVENT_DELAY)


# ---------------------------------------------------------------------- keyboard


def key_down(what: Key | str) -> None:
    safety.check()
    chosen = key(what)
    with _lock:
        if chosen not in _held_keys:
            _send(_key_event(chosen, up=False))
            _held_keys[chosen] = None
    time.sleep(EVENT_DELAY)


def key_up(what: Key | str) -> None:
    chosen = key(what)
    with _lock:
        if chosen in _held_keys:
            _send(_key_event(chosen, up=True))
            _held_keys.pop(chosen, None)
    time.sleep(EVENT_DELAY)


def tap(what: Key | str) -> None:
    key_down(what)
    key_up(what)


def write(text: str) -> None:
    """Type characters, whatever keyboard language is active. Newlines and tabs go as real keys."""
    for character in text:
        safety.check()
        if character in "\n\t":
            tap(Keys.ENTER if character == "\n" else Keys.TAB)
            continue
        data = character.encode("utf-16-le")
        with _lock:
            for at in range(0, len(data), 2):
                unit = int.from_bytes(data[at : at + 2], "little")
                _send(_unicode_event(unit, up=False))
                _send(_unicode_event(unit, up=True))
        time.sleep(EVENT_DELAY)


# ------------------------------------------------------------- the tape's input


def key_now(what: Key | str, up: bool) -> None:
    """A key down or up, sent at once with no pause after it, kept track of for release_all."""
    chosen = key(what)
    with _lock:
        if up:
            if chosen in _held_keys:
                _send(_key_event(chosen, up=True))
                _held_keys.pop(chosen, None)
        elif chosen not in _held_keys:
            _send(_key_event(chosen, up=False))
            _held_keys[chosen] = None


def button_now(button: str, up: bool) -> None:
    """A mouse button down or up where the cursor is, sent at once."""
    with _lock:
        if up:
            if button in _held_buttons:
                _send(_button_event(_BUTTONS[button][1]))
                _held_buttons.discard(button)
        elif button not in _held_buttons:
            _send(_button_event(_BUTTONS[button][0]))
            _held_buttons.add(button)


def nudge(dx: int, dy: int) -> None:
    """One relative mouse packet, like the mouse sends: what a game that holds the cursor turns its camera by."""
    event = _INPUT(type=_MOUSE)
    event.mi.dx = dx
    event.mi.dy = dy
    event.mi.dwFlags = _MOVE
    with _lock:
        _send(event)


def place(x: int, y: int) -> None:
    """Put the cursor at (x, y) at once."""
    with _lock:
        _send(_move_event(x, y))


def wheel_now(notches: int, sideways: bool = False) -> None:
    event = _INPUT(type=_MOUSE)
    event.mi.mouseData = ctypes.c_uint32(notches * 120).value
    event.mi.dwFlags = _HWHEEL if sideways else _WHEEL
    with _lock:
        _send(event)


def let_go_of_everything() -> None:
    """Send a release for every key and mouse button, held or not: after a bot is ended by force, whatever it
    was holding (W while walking) would otherwise stay down in Windows."""
    events = []
    for name in names():
        events.append(_key_event(key(name), up=True))
    for _, up_flag in _BUTTONS.values():
        events.append(_button_event(up_flag))
    with _lock:
        _send(*events)
        _held_keys.clear()
        _held_buttons.clear()


def release_all() -> None:
    """Let go of every key and mouse button darbit is holding, last pressed first."""
    with _lock:
        for held in reversed(list(_held_keys)):
            _send(_key_event(held, up=True))
        _held_keys.clear()
        for button in list(_held_buttons):
            _send(_button_event(_BUTTONS[button][1]))
        _held_buttons.clear()


safety.on_stop(release_all)
