"""What a bot shows in darbit Studio beyond its steps and events (decisions 0011 and 0013).

    d.progress("Quests this week", state.quests_done, 70)   # a ring; call again with new numbers to update it
    d.next("Weekly reset", reset_time)                        # a datetime; the Studio shows "in 2 d 4 h"
    d.record.gain("Coins", 120, total=48210, icon="◆")         # a row on the Results page: today, the week, total
    d.plan(["Quests", "Shop", "Idle"])                     # the round's order, so steps still to come show too
    d.show("Boat", 7, sub="next upgrade at 2 000 gold")      # a value of the bot's own: a block on the Overview

    @d.block("Bait left", every=60)                           # the same, asked for every minute while the bot runs
    def bait():
        return state.bait

All are run-report events, so the Studio shows the last value even when the bot isn't running.
"""

import threading
import time
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime

from . import log
from .only import wants

SHOWN_KINDS = ("number", "ring", "list", "text")  # how a value of the bot's own is drawn (the Studio picks by default)


def progress(label: str, done: float, total: float) -> None:
    """Report how far along something is: `done` of `total`."""
    if not label:
        raise ValueError("progress needs a label")
    if total <= 0:
        raise ValueError(f"progress {label!r}: total must be more than 0")
    if done < 0 or done > total:
        raise ValueError(f"progress {label!r}: done must be from 0 to {total}, not {done}")
    log.record("progress", label=label, done=done, total=total)


def next_up(label: str, at: datetime) -> None:
    """Report when something happens next (shown as `d.next`)."""
    if not label:
        raise ValueError("next needs a label")
    if not isinstance(at, datetime):
        raise TypeError(f"next {label!r}: `at` is a datetime, not {type(at).__name__}")
    log.record("next", label=label, at=at.isoformat())


def plan(steps: list[str]) -> None:
    """Report the round's top-level steps in order, so the Studio can show the ones still to come. A run started
    for one mode plans only that one."""
    names = []
    for name in steps:
        if not isinstance(name, str) or not name:
            raise ValueError(f"plan: every step is a name, not {name!r}")
        if wants(name):
            names.append(name)
    log.record("plan", steps=names)


class Record:
    """`d.record`: add an event to the run report. `d.record.gain` adds a gain for the Results page."""

    def __call__(self, event: str, **fields: object) -> None:
        log.record(event, **fields)

    def gain(self, name: str, amount: float, total: float | None = None, icon: str | None = None) -> None:
        """Report that the bot got `amount` more of `name` (coins, wood, fish), and the new total if known."""
        if not name:
            raise ValueError("gain needs a name")
        if not isinstance(amount, (int, float)) or isinstance(amount, bool):
            raise TypeError(f"gain {name!r}: amount is a number, not {type(amount).__name__}")
        fields: dict[str, object] = {"name": name, "amount": amount}
        if total is not None:
            fields["total"] = total
        if icon:
            fields["icon"] = icon
        log.record("gain", **fields)

    def recovered(self, how: str, why: str) -> None:
        """The bot got itself going again: `how` ("rejoin", "back to the menu") and `why` ("disconnected").
        Each day's results count them, the health of a bot that runs all day."""
        log.record("recovered", how=how, why=why)


def show(
    name: str,
    value: object,
    sub: str = "",
    total: float | None = None,
    unit: str = "",
    kind: str = "",
) -> None:
    """Show a value of the bot's own on darbit Studio's Overview, as a block called `name`: a number (with `total`, a
    ring), a list (`value` a list of names or of [name, value] pairs) or text. `sub` is a line under it."""
    if not name:
        raise ValueError("show needs a name")
    if kind and kind not in SHOWN_KINDS:
        raise ValueError(f"show {name!r}: kind is one of {', '.join(SHOWN_KINDS)}, not {kind!r}")
    fields: dict[str, object] = {"name": name, "value": value}
    if sub:
        fields["sub"] = sub
    if total is not None:
        fields["total"] = total
    if unit:
        fields["unit"] = unit
    if kind:
        fields["kind"] = kind
    log.record("block", **fields)


@dataclass
class _Block:
    name: str
    read: Callable[[], object]
    every: float
    last: float = 0.0


_blocks: list[_Block] = []
_lock = threading.Lock()
_started = False


def block(name: str, every: float = 30.0) -> Callable:
    """Make a function a block on the Overview: darbit asks it every `every` seconds while the bot runs and shows
    what it returns (a value, or a dict of `show`'s arguments)."""

    def register(read: Callable[[], object]) -> Callable[[], object]:
        global _started
        with _lock:
            _blocks.append(_Block(name, read, max(1.0, float(every))))
            start = not _started
            _started = True
        if start:
            threading.Thread(target=_ask_blocks, name="darbit-blocks", daemon=True).start()
        return read

    return register


def ask_blocks_once(now: float | None = None) -> None:
    """Ask each block that's due for its value and show it. A block that fails is skipped this time, not stopped."""
    moment = time.monotonic() if now is None else now
    with _lock:
        due = [one for one in _blocks if moment - one.last >= one.every or one.last == 0.0]
    for one in due:
        one.last = moment
        try:
            answer = one.read()
        except Exception as error:  # noqa: BLE001 - a broken block must not stop the bot or the other blocks
            log.log(f"block {one.name}: {error}")
            continue
        if isinstance(answer, dict):
            show(one.name, **answer)
        else:
            show(one.name, answer)


def _ask_blocks() -> None:
    while True:
        ask_blocks_once()
        time.sleep(1.0)
