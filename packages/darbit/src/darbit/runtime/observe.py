"""Observers: watch for something in the background and interrupt the script when it happens.

    d.observe("Roblox.Disconnected")                       # an image appearing
    d.observe(lambda: not d.apps.running("Roblox"), name="Roblox closed")   # a condition

    try:
        play_the_game()
    except d.Interrupted as event:
        print(event.name)                                  # which observer fired
        with d.no_interrupts():
            rejoin()

Observers only report. When one fires, held keys are let go and the next darbit call
in the script (a wait, a click, a sleep...) raises Interrupted, once. The script
decides what to do. An observer fires again only after what it watches has gone away
and come back. All image observers share one screen capture per tick.
"""

from __future__ import annotations

import threading
import time
from collections.abc import Callable
from dataclasses import dataclass, field

from ..core import matching
from ..core.geometry import Region
from ..core.targets import Target
from ..errors import Interrupted
from ..platform import safety, screen
from ..settings import settings
from .find import What, _usable
from .log import log

Condition = Callable[[], bool]


@dataclass(eq=False)
class Observer:
    name: str
    target: Target | None = None
    condition: Condition | None = None
    region: Region | None = None
    seen: bool = False  # what it watches is there now; it fires again only after this goes back to False
    fired: int = 0
    _stopped: bool = field(default=False, repr=False)

    def stop(self) -> None:
        """Stop watching."""
        self._stopped = True
        with _lock:
            if self in _observers:
                _observers.remove(self)


_observers: list[Observer] = []
_lock = threading.Lock()
_thread: threading.Thread | None = None
EVERY = 0.5  # seconds between looks


def observe(what: What | Condition, name: str | None = None, region: Region | None = None) -> Observer:
    """Watch for an image (a target name) or a condition (a function returning True), and interrupt the script
    when it shows up. Returns the Observer, to stop() it later."""
    if callable(what) and not isinstance(what, (str, Target)):
        observer = Observer(name or getattr(what, "__name__", "condition"), condition=what, region=region)
    else:
        usable = _usable((what,))
        if not usable:
            raise ValueError(f"nothing to observe: {what!r}")
        target = usable[0]
        observer = Observer(name or target.label, target=target, region=region)
    with _lock:
        _observers.append(observer)
    _start()
    log(f"observing {observer.name}")
    return observer


def observers() -> list[Observer]:
    with _lock:
        return list(_observers)


def stop_observing() -> None:
    """Stop every observer."""
    for observer in observers():
        observer.stop()


def _start() -> None:
    global _thread
    if _thread is not None and _thread.is_alive():
        return
    _thread = threading.Thread(target=_run, name="darbit-observers", daemon=True)
    _thread.start()


def _look(observer: Observer, frame: tuple | None) -> object:
    """A match or True when the observer's thing is there now, else None or False."""
    if observer.condition is not None:
        return observer.condition()
    target = observer.target
    area = observer.region or target.region
    pixels, origin = frame
    if area is not None:
        crop = area.intersect(origin)
        if crop is None:
            return None
        x, y = crop.x - origin.x, crop.y - origin.y
        pixels, origin = pixels[y : y + crop.h, x : x + crop.w], crop
    similarity = target.similarity if target.similarity is not None else settings.similarity
    return matching.best(target, pixels, origin, similarity)


def tick() -> None:
    """One look at everything observed: one screen capture shared by all image observers."""
    watching = [o for o in observers() if not o._stopped]
    frame = screen.grab() if any(o.target is not None for o in watching) else None
    for observer in watching:
        try:
            hit = _look(observer, frame)
        except Exception as error:  # noqa: BLE001 - a broken condition must not stop the other observers
            log(f"observer {observer.name} failed: {error}")
            continue
        if hit and not observer.seen:
            observer.seen = True
            observer.fired += 1
            posted = safety.interrupt(Interrupted(observer.name, hit if not isinstance(hit, bool) else None))
            log(f"observer {observer.name}: seen" + ("" if posted else " (not interrupting)"))
        elif not hit:
            observer.seen = False


def _run() -> None:
    while observers():
        started = time.monotonic()
        tick()
        time.sleep(max(0.0, EVERY - (time.monotonic() - started)))
