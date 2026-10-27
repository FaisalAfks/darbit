"""The recorder: keyboard and mouse events into an action's steps. See docs/tasks/T15-recorder.md.

The hooks (platform/hooks.py) only queue raw events; everything here is pure, so it's tested with lists of
fake events. A key pressed and let go quickly is a press (with any modifiers held: shift+e); held longer it's a
hold ... release. A left, right or middle click is a click where it happened. The time between steps becomes a
wait, rounded to 0.05 s. Checks added while paused come in as steps at the time they were added.
"""

from dataclasses import dataclass, field

from ..platform.keys import key as key_named
from ..platform.keys import names
from .flowfile import Step

PRESS_MAX = 0.15  # down and up within this many seconds is a press, longer is hold ... release
MERGE_GAP = 0.03  # gaps shorter than this aren't a wait
WAIT_STEP = 0.05  # waits are rounded to this
CLICK_MOVE = 8  # px: a press and release further apart than this is a drag, kept as a click where it started
MODIFIERS = {"shift", "ctrl", "alt", "win"}
BUTTONS = {"left": "click", "right": "right_click", "middle": "click"}


@dataclass(frozen=True)
class RawEvent:
    t: float  # seconds since the recording started
    kind: str  # "key_down", "key_up", "mouse_down", "mouse_up", "wheel"
    key: str = ""  # key name, or button: left, right, middle
    x: int = 0
    y: int = 0


@dataclass
class Timed:
    """A step and when it happened, before waits are put between them."""

    t: float
    step: Step


def key_name(vk: int) -> str:
    """The keymap name for a virtual-key code ("e", "shift", "f1"), or "" for a key darbit doesn't know."""
    if not _names_by_vk:
        for name in names():
            found = key_named(name)
            if found.vk not in _names_by_vk or len(name) < len(_names_by_vk[found.vk]):
                _names_by_vk[found.vk] = name
        for side, name in (
            (0xA0, "shift"),
            (0xA1, "shift"),
            (0xA2, "ctrl"),
            (0xA3, "ctrl"),
            (0xA4, "alt"),
            (0xA5, "alt"),
        ):
            _names_by_vk[side] = name  # left and right modifiers are the same key to a bot
    return _names_by_vk.get(vk, "")


_names_by_vk: dict[int, str] = {}


@dataclass
class Recorder:
    """Raw events while recording, with pauses and the checks added during them."""

    events: list[RawEvent] = field(default_factory=list)
    added: list[Timed] = field(default_factory=list)  # checks added while paused
    paused: bool = False

    def add(self, event: RawEvent) -> None:
        if not self.paused:
            self.events.append(event)

    def add_step(self, t: float, step: Step) -> None:
        self.added.append(Timed(t, step))

    def steps(self) -> list[Step]:
        """Every step in order, with waits between them."""
        timed = keys_to_steps(self.events) + clicks_to_steps(self.events) + list(self.added)
        timed.sort(key=_when)
        return with_waits(timed)


def _when(item: Timed) -> float:
    return item.t


def keys_to_steps(events: list[RawEvent]) -> list[Timed]:
    """Presses (with the modifiers held at the time), and holds with their releases."""
    found: list[Timed] = []
    down: dict[str, float] = {}
    used_as_modifier: set[str] = set()
    for event in events:
        if event.kind == "key_down" and event.key and event.key not in down:
            down[event.key] = event.t
            if event.key not in MODIFIERS:
                for held in down:
                    if held in MODIFIERS:
                        used_as_modifier.add(held)
        elif event.kind == "key_up" and event.key in down:
            started = down.pop(event.key)
            if event.key in MODIFIERS and event.key in used_as_modifier:
                used_as_modifier.discard(event.key)
                continue  # it was part of a combo, already in that press
            combo = []
            for held, since in down.items():
                if held in MODIFIERS and since <= started:
                    combo.append(held)
            combo.append(event.key)
            if event.t - started <= PRESS_MAX:
                found.append(Timed(started, Step("key", {"verb": "press", "keys": combo})))
            else:
                found.append(Timed(started, Step("key", {"verb": "hold", "keys": combo})))
                found.append(Timed(event.t, Step("key", {"verb": "release", "keys": combo})))
    return found


def clicks_to_steps(events: list[RawEvent]) -> list[Timed]:
    """A click where each mouse button went down."""
    found: list[Timed] = []
    down: dict[str, RawEvent] = {}
    for event in events:
        if event.kind == "mouse_down":
            down[event.key] = event
        elif event.kind == "mouse_up" and event.key in down:
            start = down.pop(event.key)
            verb = BUTTONS.get(event.key, "click")
            note = ""
            if abs(event.x - start.x) > CLICK_MOVE or abs(event.y - start.y) > CLICK_MOVE:
                note = f"was a drag to {event.x}, {event.y}"
            found.append(Timed(start.t, Step("mouse", {"verb": verb, "target": [start.x, start.y]}, note)))
    return found


def with_waits(timed: list[Timed]) -> list[Step]:
    """The steps with a wait wherever time passed between two of them."""
    found: list[Step] = []
    if not timed:
        return found
    last = timed[0].t  # the time before the first step is getting to the game, not part of the action
    for item in timed:
        gap = item.t - last
        if gap >= MERGE_GAP:
            seconds = round(round(gap / WAIT_STEP) * WAIT_STEP, 2)
            if seconds > 0:
                found.append(Step("wait", {"seconds": seconds}))
        found.append(item.step)
        last = item.t
    return found
