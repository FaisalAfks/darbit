"""The switch that keeps tests off the real PC: with DARBIT_NO_REAL_INPUT=1, every real input (mouse, keys), app
control (open, close, focus) and screen grab raises RealInputOff naming the call. Read-only calls (where the cursor
is, which windows are open, the monitors) still work. A fake put in place of a call (darbit.testing.FakeGame) is
used instead and never gets here.
"""

import os

SWITCH = "DARBIT_NO_REAL_INPUT"


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
