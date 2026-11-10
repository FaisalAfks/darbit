"""The switch that keeps tests off the real PC: with DARBIT_NO_REAL_INPUT=1, every real input (mouse, keys), app
control (open, close, focus) and screen grab raises RealInputOff naming the call. The mouse's position and the
desktop are a fixed fake (FAKE_MOUSE, FAKE_DESKTOP), so a click is refused as itself. Other read-only calls (which
windows are open, the monitors) still work. A fake put in place of a call (darbit.testing.FakeGame) is used instead
and never gets here.
"""

import os

SWITCH = "DARBIT_NO_REAL_INPUT"

# with real input off, the mouse sits in the bottom right corner of a 1920x1080 desktop: away from where a test
# clicks, so a click (with `approach` on too) goes straight to the switch and is refused as input.click, and the
# same on every system, with or without its pieces
FAKE_DESKTOP = (0, 0, 1920, 1080)
FAKE_MOUSE = (1919, 1079)


class RealInputOff(RuntimeError):
    """A test reached the real mouse, keys, apps or screen while DARBIT_NO_REAL_INPUT=1."""


def off() -> bool:
    """Whether real input is switched off (looked at on every call, so a test can turn it on or off)."""
    return os.environ.get(SWITCH, "") not in ("", "0")


def refuse(call: str) -> None:
    """Raise if real input is off: `call` names what would have touched the PC."""
    if off():
        raise RealInputOff(
            f"{call}: real input is off ({SWITCH}=1). Put a fake in its place (darbit.testing.FakeGame) "
            "or replace the call in the test"
        )
