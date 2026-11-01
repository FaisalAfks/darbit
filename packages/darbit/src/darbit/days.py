"""Which day a moment belongs to. A bot's day can start at another time than midnight: `[settings] day_starts` in its
darbit.toml, "03:00" (this PC's clock) or "00:00 UTC" (a game that resets at midnight UTC, whatever the PC's clock).
Everything in darbit that names a day asks here: the run report and the log (their files), history, the Studio's
Overview and Results, and the daily summary.
"""

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

MIDNIGHT = "00:00"


@dataclass(frozen=True)
class DayStart:
    """When a day starts: a time on this PC's clock, or in UTC."""

    hour: int = 0
    minute: int = 0
    utc: bool = False


def parse(text: object) -> DayStart:
    """`day_starts` as written: "03:00", "3:30" or "00:00 UTC". ValueError says what's wrong."""
    words = str(text or MIDNIGHT).strip().split()
    utc = len(words) == 2 and words[1].upper() == "UTC"
    if len(words) not in (1, 2) or (len(words) == 2 and not utc):
        raise ValueError(f'day_starts is "{text}": write a time like "03:00", or "00:00 UTC"')
    hour, _, minute = words[0].partition(":")
    try:
        start = DayStart(int(hour), int(minute or 0), utc)
    except ValueError:
        raise ValueError(f'day_starts is "{text}": write a time like "03:00", or "00:00 UTC"') from None
    if not (0 <= start.hour < 24 and 0 <= start.minute < 60):
        raise ValueError(f'day_starts is "{text}": the hour is 0 to 23 and the minutes 0 to 59')
    return start


def day_of(moment: datetime, start: DayStart) -> str:
    """The day ("2026-11-02") a moment belongs to. A moment without a time zone is on this PC's clock."""
    if start.utc:
        moment = moment.astimezone(UTC)
    return (moment - timedelta(hours=start.hour, minutes=start.minute)).strftime("%Y-%m-%d")


def today(start: DayStart, now: datetime | None = None) -> str:
    """The day it is now."""
    return day_of(now or datetime.now(), start)


def of(settings: dict) -> DayStart:
    """A bot's day start from its darbit settings; midnight when it names none or names one wrongly."""
    try:
        return parse(settings.get("day_starts", MIDNIGHT))
    except ValueError:
        return DayStart()
