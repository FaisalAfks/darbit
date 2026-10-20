"""Keys by physical position, not by letter.

The letter printed on a key depends on the keyboard layout; its position does not.
SikuliX asked the active layout what key makes a "w" (VkKeyScan), which fails
outright on an Arabic or Russian layout and silently sends the wrong thing on a
French one. Here a key is a *place on the keyboard*: `W` is the key right of `Q`,
whatever it prints.

Each key carries its set-1 scan code (the position) and its US virtual-key code,
and both are sent, so games that read raw input and apps that read virtual keys
both get something sensible whatever layout is active.

For real text, don't press keys at all: `input.write("héllo")` types characters
directly and doesn't care about layouts either.
"""
from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType

from ..errors import UnknownKey


@dataclass(frozen=True)
class Key:
    """One physical key."""

    name: str
    scan: int  # set-1 scan code: the position
    vk: int  # US virtual-key code
    extended: bool = False  # keys Windows prefixes with E0 (arrows, insert, ...)

    def __str__(self) -> str:
        return self.name


def _letters() -> dict[str, Key]:
    rows = [("qwertyuiop", 0x10), ("asdfghjkl", 0x1E), ("zxcvbnm", 0x2C)]
    keys = {}
    for row, first_scan in rows:
        for index, letter in enumerate(row):
            keys[letter] = Key(letter, first_scan + index, ord(letter.upper()))
    return keys


def _digits() -> dict[str, Key]:
    # 1..9 then 0, the way they sit on the row
    return {digit: Key(digit, 0x02 + index, ord(digit))
            for index, digit in enumerate("1234567890")}


_KEYS = {**_letters(), **_digits()}  # _add() puts the named keys in; read-only once Keys is built


def _add(name: str, scan: int, vk: int, extended: bool = False, *aliases: str) -> Key:
    key = Key(name, scan, vk, extended)
    _KEYS[name] = key
    for alias in aliases:
        _KEYS[alias] = key
    return key


class Keys:
    """Named keys. Letters and digits are also reachable as strings: press("w")."""

    ESC = _add("esc", 0x01, 0x1B, False, "escape")
    BACKSPACE = _add("backspace", 0x0E, 0x08)
    TAB = _add("tab", 0x0F, 0x09)
    ENTER = _add("enter", 0x1C, 0x0D, False, "return")
    CTRL = _add("ctrl", 0x1D, 0x11, False, "control")
    SHIFT = _add("shift", 0x2A, 0x10)
    ALT = _add("alt", 0x38, 0x12, False, "menu")
    SPACE = _add("space", 0x39, 0x20)
    CAPS_LOCK = _add("capslock", 0x3A, 0x14)

    MINUS = _add("-", 0x0C, 0xBD)
    EQUALS = _add("=", 0x0D, 0xBB)
    LEFT_BRACKET = _add("[", 0x1A, 0xDB)
    RIGHT_BRACKET = _add("]", 0x1B, 0xDD)
    SEMICOLON = _add(";", 0x27, 0xBA)
    QUOTE = _add("'", 0x28, 0xDE)
    BACKQUOTE = _add("`", 0x29, 0xC0)
    BACKSLASH = _add("\\", 0x2B, 0xDC)
    COMMA = _add(",", 0x33, 0xBC)
    PERIOD = _add(".", 0x34, 0xBE)
    SLASH = _add("/", 0x35, 0xBF)

    # the E0 group: Windows marks these as extended
    INSERT = _add("insert", 0x52, 0x2D, True)
    DELETE = _add("delete", 0x53, 0x2E, True, "del")
    HOME = _add("home", 0x47, 0x24, True)
    END = _add("end", 0x4F, 0x23, True)
    PAGE_UP = _add("pageup", 0x49, 0x21, True, "pgup")
    PAGE_DOWN = _add("pagedown", 0x51, 0x22, True, "pgdn")
    UP = _add("up", 0x48, 0x26, True)
    LEFT = _add("left", 0x4B, 0x25, True)
    RIGHT = _add("right", 0x4D, 0x27, True)
    DOWN = _add("down", 0x50, 0x28, True)

    F1 = _add("f1", 0x3B, 0x70)
    F2 = _add("f2", 0x3C, 0x71)
    F3 = _add("f3", 0x3D, 0x72)
    F4 = _add("f4", 0x3E, 0x73)
    F5 = _add("f5", 0x3F, 0x74)
    F6 = _add("f6", 0x40, 0x75)
    F7 = _add("f7", 0x41, 0x76)
    F8 = _add("f8", 0x42, 0x77)
    F9 = _add("f9", 0x43, 0x78)
    F10 = _add("f10", 0x44, 0x79)
    F11 = _add("f11", 0x57, 0x7A)
    F12 = _add("f12", 0x58, 0x7B)


_KEYS = MappingProxyType(_KEYS)  # every backend shares this one table, so nobody may change it


def key(what: Key | str) -> Key:
    """A Key from a Key, a letter, a digit or a name like "enter" or "pageup"."""
    if isinstance(what, Key):
        return what
    found = _KEYS.get(str(what).strip().lower())
    if found is None:
        raise UnknownKey(f"no key called {what!r}; use a name from Keys, or write() for text")
    return found


def keys(text: str) -> list[Key]:
    """The keys for a run of characters, e.g. "54132" or "qerzx"."""
    return [key(character) for character in text]


def names() -> list[str]:
    return sorted(_KEYS)
