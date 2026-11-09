"""Running one mode or one step of a bot instead of its whole round (decision 0022).

The service starts a bot with DARBIT_ONLY set to {"mode": ..., "step": ...} (the step left out for a whole mode).
`d.only()` says what was asked, and `d.wants(mode, step)` whether a mode or a step should run:

    for mode in ["Daily quest", "Shop"]:
        if d.wants(mode):
            with d.step(mode):
                ...
    if d.only():
        return  # one mode or step: the round is over
"""

import json
import os
from dataclasses import dataclass

ONLY = "DARBIT_ONLY"  # the environment variable the service sets


@dataclass(frozen=True)
class Only:
    """The one mode, or the one step of a mode, a run was started for."""

    mode: str
    step: str = ""

    def __str__(self) -> str:
        return f"{self.mode} › {self.step}" if self.step else self.mode


def only() -> Only | None:
    """The mode or step this run was started for; None for a whole round."""
    text = os.environ.get(ONLY, "")
    if not text:
        return None
    try:
        asked = json.loads(text)
    except ValueError:
        raise ValueError(f'{ONLY} is JSON like {{"mode": "Shop"}}, not {text!r}') from None
    if not isinstance(asked, dict) or not asked.get("mode"):
        raise ValueError(f'{ONLY} names a mode, like {{"mode": "Shop"}}, not {text!r}')
    return Only(str(asked["mode"]), str(asked.get("step") or ""))


def wants(mode: str, step: str = "") -> bool:
    """Whether this run does `mode`, or `step` of it: always in a whole round, else only the one asked for."""
    asked = only()
    if asked is None:
        return True
    if mode != asked.mode:
        return False
    return not step or not asked.step or step == asked.step
