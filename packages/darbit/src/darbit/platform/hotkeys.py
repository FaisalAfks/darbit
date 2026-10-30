"""Global hotkeys from the keymap's [global] scope. See docs/archive/tasks/T04-keymap.md.

RegisterHotKey on one thread with its own message loop: Windows calls back even while a game is in front.
A key Windows won't give (another program holds it) is skipped and named in the result, so one taken key
never stops the others. Handlers run on their own thread, so a slow one never blocks the next press.
"""

import ctypes
import threading
from collections.abc import Callable
from ctypes import wintypes

from .keys import key

MOD_ALT = 0x0001
MOD_CONTROL = 0x0002
MOD_SHIFT = 0x0004
MOD_WIN = 0x0008
MOD_NOREPEAT = 0x4000  # holding the keys down fires once
WM_HOTKEY = 0x0312
WM_QUIT = 0x0012
MODIFIERS = {"ctrl": MOD_CONTROL, "control": MOD_CONTROL, "alt": MOD_ALT, "shift": MOD_SHIFT, "win": MOD_WIN}


def parse(combo: str) -> tuple[int, int]:
    """A combo like ctrl+alt+c as Windows modifier bits and the main key's virtual-key code."""
    modifiers = MOD_NOREPEAT
    main = None
    for part in combo.lower().split("+"):
        name = part.strip()
        if name in MODIFIERS:
            modifiers |= MODIFIERS[name]
        elif main is None:
            main = key(name).vk
        else:
            raise ValueError(f"{combo!r}: a hotkey has one main key")
    if main is None:
        raise ValueError(f"{combo!r}: no main key")
    return modifiers, main


class Registered:
    """Hotkeys that are live. `stop()` lets go of them; `missing` names the ones Windows refused."""

    def __init__(self) -> None:
        self.thread_id = 0
        self.missing: list[str] = []
        self.ready = threading.Event()

    def stop(self) -> None:
        ctypes.windll.user32.PostThreadMessageW(self.thread_id, WM_QUIT, 0, 0)


def register(keys: dict[str, str], handlers: dict[str, Callable[[], None]]) -> Registered:
    """Register each action's keys; pressing them calls its handler. Actions without a handler are skipped."""
    user32 = ctypes.windll.user32
    wanted: list[tuple[str, int, int]] = []
    for action, combo in keys.items():
        if action in handlers and combo:
            modifiers, vk = parse(combo)
            wanted.append((action, modifiers, vk))
    registered = Registered()

    def loop() -> None:
        registered.thread_id = ctypes.windll.kernel32.GetCurrentThreadId()
        actions: dict[int, str] = {}
        for number, (action, modifiers, vk) in enumerate(wanted, start=1):
            if user32.RegisterHotKey(None, number, modifiers, vk):
                actions[number] = action
            else:
                registered.missing.append(action)
        registered.ready.set()
        message = wintypes.MSG()
        while user32.GetMessageW(ctypes.byref(message), None, 0, 0) > 0:
            if message.message == WM_HOTKEY and message.wParam in actions:
                handler = handlers[actions[message.wParam]]
                threading.Thread(target=handler, name="darbit-hotkey", daemon=True).start()
        for number in actions:
            user32.UnregisterHotKey(None, number)

    threading.Thread(target=loop, name="darbit-hotkeys", daemon=True).start()
    registered.ready.wait(2)
    return registered
