"""The recorder: keyboard and mouse events into an action's steps. See docs/tasks/T15-recorder.md.

The hooks (platform/hooks.py) only queue raw events; everything here is pure, so it's tested with lists of
fake events. A key pressed and let go quickly is a press (with any modifiers held: shift+e); held longer it's a
hold ... release. A left, right or middle click is a click where it happened. The time between steps becomes a
wait, rounded to 0.01 s. Checks added while paused come in as steps at the time they were added. Mouse movement is
kept as the mouse's own counts (move_by), which Windows and games treat like a hand on the mouse: the cursor follows
the same path, and a game that holds the cursor (Roblox's shift lock) turns its camera the same. The wheel is kept too.
"""

from dataclasses import dataclass, field

from ..platform.keys import key as key_named
from ..platform.keys import names
from .flowfile import Step

PRESS_MAX = 0.15  # down and up within this many seconds is a press, longer is hold ... release
MERGE_GAP = 0.01  # gaps shorter than this aren't a wait
WAIT_STEP = 0.01  # waits are rounded to this
MOVE_PART = 0.1  # seconds of mouse movement kept as one move_by step
MOVE_GAP = 0.05  # a pause this long in the movement starts a new move_by
WHEEL_GAP = 0.15  # wheel notches closer together than this are one scroll
CLICK_MOVE = 8  # px: a press and release further apart than this is a drag, kept as a click where it started
MODIFIERS = {"shift", "ctrl", "alt", "win"}
BUTTONS = {"left": "click", "right": "right_click", "middle": "click"}


@dataclass(frozen=True)
class RawEvent:
    t: float  # seconds since the recording started
    kind: str  # "key_down", "key_up", "mouse_down", "mouse_up", "wheel", "move"
    key: str = ""  # key name, or button: left, right, middle
    x: int = 0  # where the cursor was
    y: int = 0
    dx: int = 0  # "move": how far the mouse itself moved, in counts; "wheel": notches (up is positive)
    dy: int = 0


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
        timed = keys_to_steps(self.events) + clicks_to_steps(self.events) + moves_to_steps(self.events)
        timed += wheel_to_steps(self.events) + self.added
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
                pressed = ["+".join(combo)]  # one press of shift+e, not shift then e
                found.append(Timed(started, Step("key", {"verb": "press", "keys": pressed})))
            else:
                found.append(Timed(started, Step("key", {"verb": "hold", "keys": combo})))
                found.append(Timed(event.t, Step("key", {"verb": "release", "keys": combo})))
    return found


def clicks_to_steps(events: list[RawEvent]) -> list[Timed]:
    """A click where each mouse button went down; a drag (the mouse moved while it was down, like turning Roblox's
    camera with the right button) is the button going down, then up, so the movement in between plays with it held."""
    found: list[Timed] = []
    down: dict[str, RawEvent] = {}
    moved_while_down: dict[str, int] = {}  # counts the mouse moved while each button was down
    for event in events:
        if event.kind == "move":
            for button in down:
                moved_while_down[button] += abs(event.dx) + abs(event.dy)
        elif event.kind == "mouse_down":
            down[event.key] = event
            moved_while_down[event.key] = 0
        elif event.kind == "mouse_up" and event.key in down:
            start = down.pop(event.key)
            moved = abs(event.x - start.x) > CLICK_MOVE or abs(event.y - start.y) > CLICK_MOVE
            if moved or moved_while_down.get(event.key, 0) > CLICK_MOVE:
                found.append(Timed(start.t, _button_step("mouse_down", event.key, [start.x, start.y])))
                end = None  # let go where it is: moving a held button would turn the camera again
                if moved:
                    end = [event.x, event.y]
                found.append(Timed(event.t, _button_step("mouse_up", event.key, end)))
            else:
                verb = BUTTONS.get(event.key, "click")
                found.append(Timed(start.t, Step("mouse", {"verb": verb, "target": [start.x, start.y]})))
    return found


def _button_step(verb: str, button: str, target: list[int] | None) -> Step:
    return Step("mouse", {"verb": verb, "target": target, "button": button})


def moves_to_steps(events: list[RawEvent]) -> list[Timed]:
    """Mouse movement as move_by steps of the mouse's own counts, one for every short stretch of moving."""
    found: list[Timed] = []
    part: list[RawEvent] = []
    for event in events:
        if event.kind != "move":
            if part and event.kind in ("mouse_down", "mouse_up", "wheel"):
                _add_move(part, found)  # the movement before a click ends before it
                part = []
            continue
        if part and (event.t - part[0].t >= MOVE_PART or event.t - part[-1].t > MOVE_GAP):
            _add_move(part, found)
            part = []
        part.append(event)
    if part:
        _add_move(part, found)
    return found


def _add_move(part: list[RawEvent], found: list[Timed]) -> None:
    dx = 0
    dy = 0
    for event in part:
        dx += event.dx
        dy += event.dy
    if dx == 0 and dy == 0:
        return
    seconds = round(part[-1].t - part[0].t, 2)
    found.append(Timed(part[0].t, Step("mouse", {"verb": "move_by", "by": [dx, dy], "seconds": seconds})))


def wheel_to_steps(events: list[RawEvent]) -> list[Timed]:
    """The wheel: notches close together are one scroll."""
    found: list[Timed] = []
    started = 0.0
    last = -1.0
    notches = 0
    for event in events:
        if event.kind != "wheel":
            continue
        if notches and event.t - last <= WHEEL_GAP and (event.dx > 0) == (notches > 0):
            notches += event.dx
        else:
            if notches:
                found.append(Timed(started, Step("mouse", {"verb": "scroll", "notches": notches})))
            started = event.t
            notches = event.dx
        last = event.t
    if notches:
        found.append(Timed(started, Step("mouse", {"verb": "scroll", "notches": notches})))
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
