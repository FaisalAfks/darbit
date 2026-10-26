"""What a bot shows in darbit Studio beyond its steps and events (decision 0011): progress and what's next.

    d.progress("Speed Raid this week", state.sr_done, 133)   # a ring; call again with new numbers to update it
    d.next("Weekly reset", reset_time)                        # a datetime; the Studio shows "in 2 d 4 h"

Both are run-report events, so the Studio shows the last value even when the bot isn't running.
"""

from datetime import datetime

from .log import record


def progress(label: str, done: float, total: float) -> None:
    """Report how far along something is: `done` of `total`."""
    if not label:
        raise ValueError("progress needs a label")
    if total <= 0:
        raise ValueError(f"progress {label!r}: total must be more than 0")
    if done < 0 or done > total:
        raise ValueError(f"progress {label!r}: done must be from 0 to {total}, not {done}")
    record("progress", label=label, done=done, total=total)


def next_up(label: str, at: datetime) -> None:
    """Report when something happens next (shown as `d.next`)."""
    if not label:
        raise ValueError("next needs a label")
    if not isinstance(at, datetime):
        raise TypeError(f"next {label!r}: `at` is a datetime, not {type(at).__name__}")
    record("next", label=label, at=at.isoformat())
