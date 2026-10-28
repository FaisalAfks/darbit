"""Mouse and keyboard actions on targets, matches and locations."""

import threading
import time

from ..core.geometry import Location, Region
from ..core.targets import Match, Target
from ..platform import input as device
from ..platform import safety, windows
from ..platform.keys import Key
from ..settings import settings
from .find import What, _usable, wait
from .log import log, record

Spot = What | Match | Location


def _front() -> None:
    """Bring settings.window to the front if it's set, open and behind something."""
    if not settings.window:
        return
    found = windows.matching(settings.window)
    if found and not windows.in_front(found[0].handle):
        windows.bring_to_front(found[0].handle)


def _point(what: Spot, timeout: float | None, region: Region | None) -> tuple[int, int] | None:
    """Where an action lands: a location as is, a match's click point, or a target found within `timeout`."""
    if isinstance(what, Location):
        return what.point()
    if isinstance(what, Match):
        return what.point.point()
    usable = _usable((what,))
    if not usable:
        return None
    chosen = usable[0]
    if chosen._pixels is None:  # a target that's only a location
        return chosen.location.point() if chosen.location is not None else None
    found = wait(chosen, timeout=timeout, region=region)
    return found.point.point() if found is not None else None


def _label(what: Spot) -> str:
    if isinstance(what, Match):
        return what.name or "match"
    if isinstance(what, Target):
        return what.label
    return str(what)


def _mouse(kind: str, what: Spot, timeout: float | None, region: Region | None, button: str, times: int) -> bool:
    point = _point(what, timeout, region)
    if point is None:
        log(f"{kind} {_label(what)}: not found")
        record(kind, target=_label(what), done=False)
        return False
    _front()
    device.click(*point, _glide(), button, times)
    log(f"{kind} {_label(what)} at {point[0]},{point[1]}")
    record(kind, target=_label(what), done=True, at=list(point))
    return True


def click(what: Spot, timeout: float | None = None, region: Region | None = None) -> bool:
    """Click a target, match or location. False if the target isn't found in time."""
    return _mouse("click", what, timeout, region, "left", 1)


def double_click(what: Spot, timeout: float | None = None, region: Region | None = None) -> bool:
    return _mouse("double_click", what, timeout, region, "left", 2)


def right_click(what: Spot, timeout: float | None = None, region: Region | None = None) -> bool:
    return _mouse("right_click", what, timeout, region, "right", 1)


def hover(what: Spot, timeout: float | None = None, region: Region | None = None) -> bool:
    """Move the mouse onto a target, match or location."""
    point = _point(what, timeout, region)
    if point is None:
        return False
    _front()
    device.move(*point, _glide())
    return True


def drag(what: Spot, to: Spot, timeout: float | None = None, region: Region | None = None) -> bool:
    """Drag from one spot to another, like SikuliX's dragDrop. `region` applies to finding `what`."""
    start = _point(what, timeout, region)
    end = _point(to, timeout, None) if start is not None else None
    if start is None or end is None:
        log(f"drag {_label(what)} -> {_label(to)}: not found")
        record("drag", target=_label(what), done=False)
        return False
    _front()
    device.drag(*start, *end, settings.glide)
    log(f"drag {_label(what)} {start} -> {end}")
    record("drag", target=_label(what), done=True, at=list(start), to=list(end))
    return True


def scroll(notches: int, at: Spot | None = None) -> bool:
    """Turn the mouse wheel: positive scrolls up, negative down. Moves to `at` first if given."""
    if at is not None and not hover(at):
        return False
    _front()
    device.scroll(notches)
    return True


# ---------------------------------------------------------------------- keyboard


def press(*keys: Key | str) -> None:
    """Press and let go of each key in order: press("tab"), press(*"54132"), press("ctrl+a")."""
    _front()
    for one in keys:
        if isinstance(one, str) and "+" in one and len(one) > 1:
            parts = one.split("+")
            for part in parts[:-1]:
                device.key_down(part)
            try:
                device.tap(parts[-1])
            finally:
                for part in reversed(parts[:-1]):
                    device.key_up(part)
        else:
            device.tap(one)


def hold(*keys: Key | str) -> None:
    """Keep keys down until release()."""
    _front()
    for one in keys:
        device.key_down(one)


def release(*keys: Key | str) -> None:
    """Let go of the given keys, or of every held key and button when none are given."""
    if not keys:
        device.release_all()
        return
    for one in keys:
        device.key_up(one)


def write(text: str) -> None:
    """Type text as characters, in any keyboard language. Games that read key positions want press()."""
    _front()
    device.write(text)


def mouse_down(at: Spot | None = None, button: str = "left") -> bool:
    """Press a mouse button and keep it down until mouse_up(), at `at` if given, else where the mouse is."""
    if at is not None and not hover(at):
        return False
    _front()
    device.mouse_down(button)
    return True


def mouse_up(at: Spot | None = None, button: str = "left") -> bool:
    """Let go of a mouse button, after moving to `at` if given (the end of a drag)."""
    if at is not None and not hover(at):
        return False
    device.mouse_up(button)
    return True


def move_by(dx: int, dy: int, seconds: float = 0) -> None:
    """Move the mouse by dx, dy counts over `seconds`, like a hand on the mouse: turns a game's camera even when the
    game holds the cursor in place (Roblox's shift lock)."""
    _front()
    device.move_by(dx, dy, seconds)


def sleep(seconds: float) -> None:
    """Wait, stopping at once if the stop hotkey is pressed. In a timed action, wait until `seconds` after the
    previous wait was due, so the time the steps between took doesn't add up."""
    schedule = _timeline()
    if schedule is None:
        safety.sleep(seconds)
        return
    now = time.perf_counter()
    if now - schedule.due > LATE_LIMIT:
        schedule.due = now  # something slow ran (a picture check): carry on from here
    schedule.due += seconds
    safety.sleep(max(0.0, schedule.due - time.perf_counter()))


# ---- timed actions (recorded ones): waits keep to the recorded schedule

LATE_LIMIT = 0.5  # seconds behind schedule that are caught up; later than this, the schedule starts again
TIMED_GLIDE = 0.03  # seconds a click glides in a timed action: enough for a game to see the hover


class _Schedule:
    def __init__(self) -> None:
        self.due = time.perf_counter()


_timelines = threading.local()


def _timeline() -> _Schedule | None:
    return getattr(_timelines, "current", None)


def start_timeline() -> _Schedule | None:
    """Waits keep to a schedule from now on, in this thread. Returns the one before, for end_timeline."""
    before = _timeline()
    _timelines.current = _Schedule()
    return before


def end_timeline(before: _Schedule | None) -> None:
    _timelines.current = before


def _glide() -> float:
    if _timeline() is None:
        return settings.glide
    return min(settings.glide, TIMED_GLIDE)
