"""What a bot shows in darbit Studio beyond its steps and events (decisions 0011 and 0013).

    d.progress("Speed Raid this week", state.sr_done, 133)   # a ring; call again with new numbers to update it
    d.next("Weekly reset", reset_time)                        # a datetime; the Studio shows "in 2 d 4 h"
    d.record.gain("Gems", 120, total=48210, icon="◆")         # a row on the Results page: today, the week, total
    d.plan(["Raid", "Speed Raid", "AFK"])                     # the round's order, so steps still to come show too

All are run-report events, so the Studio shows the last value even when the bot isn't running.
"""

from datetime import datetime

from . import log


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
    """Report the round's top-level steps in order, so the Studio can show the ones still to come."""
    names = []
    for name in steps:
        if not isinstance(name, str) or not name:
            raise ValueError(f"plan: every step is a name, not {name!r}")
        names.append(name)
    log.record("plan", steps=names)


class Record:
    """`d.record`: add an event to the run report. `d.record.gain` adds a gain for the Results page."""

    def __call__(self, event: str, **fields: object) -> None:
        log.record(event, **fields)

    def gain(self, name: str, amount: float, total: float | None = None, icon: str | None = None) -> None:
        """Report that the bot got `amount` more of `name` (gems, gold, fish), and the new total if known."""
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
