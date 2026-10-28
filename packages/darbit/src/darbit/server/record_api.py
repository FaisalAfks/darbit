"""Recording an action from darbit Studio (decision 0013, round 8; T15).

`record.start` (through the desktop, which hides the Studio and shows the recorder bar) starts the keyboard and
mouse hooks; every real key and click goes to a Recorder. `record.pause` toggles pausing; while paused,
`record.check` adds a wait or a picture check at that moment. `record.stop` writes `actions/<name>.py` and
tells the Studio to open it. A `record.tick` event several times a second feeds the bar and its live steps.

Left out of the recording: darbit's own hotkeys (anything pressed with Ctrl and Alt both down) and clicks on
the recorder bar itself.
"""

import threading
import time
from collections.abc import Callable
from dataclasses import dataclass, field, replace
from pathlib import Path

from .. import __version__
from ..platform import hooks, switching
from ..platform import input as device
from ..project import manifest
from ..runs.flowfile import Step, statement, to_dict
from ..runs.recorder import RawEvent, Recorder, key_name
from ..runtime import tape
from ..settings import settings
from . import actions_api
from .events import publish

TICK = 0.25  # seconds between record.tick events
TAIL = 0.05  # seconds kept after the last event
MARK_GAP = 0.2  # a second checkpoint this soon after one is the same one
SHOWN_STEPS = 14  # steps sent with each tick, newest last
BUTTONS = {0: "left", 1: "right", 2: "middle"}

ignore_area: Callable[[], tuple[int, int, int, int] | None] | None = (
    None  # the bar's screen rectangle, from the desktop
)
on_end: Callable[[str | None], None] | None = None  # the desktop closes the bar and opens the action (None: cancelled)


@dataclass
class Recording:
    project: Path
    name: str
    recorder: Recorder = field(default_factory=Recorder)
    started: float = field(default_factory=time.perf_counter)
    stop_hooks: Callable[[], None] | None = None
    slow_again: Callable[[], None] | None = None  # ends the quick thread switching
    cursor: tuple[int, int] = (0, 0)  # where the cursor last was
    window: list[int] | None = None  # the game window's client area when recording started
    screen: list[int] | None = None
    held: set[str] = field(default_factory=set)  # keys down right now
    hotkey_keys: set[str] = field(default_factory=set)  # keys of a darbit hotkey: their ups are dropped too
    running: threading.Event = field(default_factory=threading.Event)
    marks: list[float] = field(default_factory=list)  # checkpoints: each one ends a part, saved as its own action
    paused_since: float | None = None  # perf_counter when the pause began
    paused_for: float = 0.0  # seconds paused so far, left out of the recording's clock

    def seconds(self) -> float:
        """The recording's clock: time since it started, without the time it was paused."""
        now = time.perf_counter()
        if self.paused_since is not None:
            now = self.paused_since
        return now - self.started - self.paused_for


_recording: Recording | None = None


def _inside_bar(x: int, y: int) -> bool:
    if ignore_area is None:
        return False
    area = ignore_area()
    if area is None:
        return False
    left, top, width, height = area
    return left <= x < left + width and top <= y < top + height


def _on_event(kind: str, code: int, x: int, y: int, time_ns: int) -> None:
    recording = _recording
    if recording is None:
        return
    t = time_ns / 1e9 - recording.started - recording.paused_for
    if kind in ("key_down", "key_up"):
        _on_key(recording, kind, key_name(code), t)
    elif kind in ("mouse_down", "mouse_up"):
        if _inside_bar(x, y):
            return
        recording.recorder.add(RawEvent(t, kind, BUTTONS.get(code, "left"), x, y))
    elif kind == "mouse_move":
        recording.cursor = (x, y)
    elif kind == "mouse_delta":
        cursor_x, cursor_y = recording.cursor
        recording.recorder.add(RawEvent(t, "move", "", cursor_x, cursor_y, x, y, shown=code == 1))
    elif kind in ("wheel", "hwheel"):
        if _inside_bar(x, y):
            return
        recording.recorder.add(RawEvent(t, kind, "", x, y, code))


def _on_key(recording: Recording, kind: str, name: str, t: float) -> None:
    if not name:
        return
    if kind == "key_down":
        recording.held.add(name)
        if "ctrl" in recording.held and "alt" in recording.held:
            _drop_hotkey(recording)
            recording.hotkey_keys.add(name)
            return
    else:
        recording.held.discard(name)
        if name in recording.hotkey_keys:
            recording.hotkey_keys.discard(name)
            return
    recording.recorder.add(RawEvent(t, kind, name))


def _drop_hotkey(recording: Recording) -> None:
    """Ctrl and Alt are both down: that's a darbit hotkey, so forget the modifiers' downs already recorded."""
    for modifier in ("ctrl", "alt", "shift"):
        if modifier in recording.held:
            recording.hotkey_keys.add(modifier)
    kept = []
    for event in recording.recorder.events:
        if event.kind == "key_down" and event.key in recording.hotkey_keys and event.key in recording.held:
            continue
        kept.append(event)
    recording.recorder.events = kept


def start(project: Path, name: str, replace: bool = False) -> dict:
    """Start recording into actions/<name>.py; an existing action is only replaced with `replace` (Re-record)."""
    global _recording
    if not name.isidentifier():
        raise ValueError(f"{name!r} can't be an action's name: use letters, digits and _")
    if _recording is not None:
        raise ValueError("already recording")
    if not replace and (project / "actions" / f"{name}.py").exists():
        raise ValueError(f"{name} already exists: open it and use Re-record to replace it")
    recording = Recording(project, name)
    manifest.setup(settings, __version__, project)  # the bot's settings.window: places are kept relative to it
    recording.window = tape._window_now()
    recording.screen = list(device.desktop())
    _recording = recording
    recording.slow_again = switching.fast()  # the raw input thread mustn't wait its turn: counts were lost
    recording.stop_hooks = hooks.start(_on_event, moves=True)  # the cursor's place goes with each mouse packet
    recording.running.set()
    threading.Thread(target=_tick, args=(recording,), name="darbit-record-tick", daemon=True).start()
    return status()


def status() -> dict:
    recording = _recording
    if recording is None:
        return {"recording": False}
    steps = recording.recorder.steps()
    shown = []
    for step in steps[-SHOWN_STEPS:]:
        shown.append({"kind": step.kind, "text": statement(step), "note": step.note})
    checks = 0
    for step in steps:
        if step.kind == "check":
            checks += 1
    return {
        "recording": True,
        "name": recording.name,
        "path": str(recording.project),
        "seconds": round(recording.seconds(), 1),
        "paused": recording.recorder.paused,
        "count": len(steps),
        "checks": checks,
        "parts": len(recording.marks) + 1,
        "steps": shown,
    }


def _tick(recording: Recording) -> None:
    while recording.running.is_set():
        publish("record.tick", status())
        time.sleep(TICK)


def pause() -> dict:
    """Pause or go on. Keys held when pausing are let go on the tape then, and paused time is left out."""
    recording = _current()
    if recording.paused_since is None:
        t = recording.seconds()
        for name in sorted(recording.held - recording.hotkey_keys):
            recording.recorder.add(RawEvent(t, "key_up", name))
        recording.recorder.paused = True
        recording.paused_since = time.perf_counter()
    else:
        recording.paused_for += time.perf_counter() - recording.paused_since
        recording.paused_since = None
        recording.recorder.paused = False
    publish("record.tick", status())
    return status()


def mark() -> dict:
    """A checkpoint: everything since the last one becomes its own action (decision 0014)."""
    recording = _current()
    t = recording.seconds()
    if not recording.marks or t - recording.marks[-1] > MARK_GAP:
        recording.marks.append(t)
    publish("record.tick", status())
    return status()


def add_check(data: dict) -> dict:
    """While paused: a wait, or a picture to wait for (or that must be gone), at this moment."""
    recording = _current()
    kind = str(data.get("kind", "wait"))
    if kind == "wait":
        step = Step("wait", {"seconds": float(data.get("seconds") or 1)})
    elif kind == "picture":
        target = str(data.get("target") or "")
        if not target:
            raise ValueError("pick the picture to wait for")
        verb = "until gone" if data.get("gone") else "wait for"
        step = Step("check", {"verb": verb, "target": target, "timeout": float(data.get("timeout") or 30)})
    else:
        raise ValueError(f"no check called {kind}")
    recording.recorder.add_step(recording.seconds(), step)
    publish("record.tick", status())
    return status()


def remove_last() -> dict:
    """Forget the last thing recorded (a wrong click), without stopping."""
    recording = _current()
    events = recording.recorder.events
    if recording.recorder.added and (not events or recording.recorder.added[-1].t >= events[-1].t):
        recording.recorder.added.pop()
    else:
        _drop_last_action(recording)
    publish("record.tick", status())
    return status()


def _drop_last_action(recording: Recording) -> None:
    events = recording.recorder.events
    if not events:
        return
    last = events[-1]
    downs = {"key_up": "key_down", "mouse_up": "mouse_down"}
    pair = downs.get(last.kind)
    events.pop()
    if pair is None:
        return
    for index in range(len(events) - 1, -1, -1):
        if events[index].kind == pair and events[index].key == last.key:
            events.pop(index)
            return


def stop(keep: bool = True) -> dict:
    """Stop recording; with `keep`, write the action and open it in the Studio."""
    global _recording
    recording = _current()
    _recording = None
    recording.running.clear()
    if recording.stop_hooks is not None:
        recording.stop_hooks()
    if recording.slow_again is not None:
        recording.slow_again()
    result: dict = {"saved": False}
    if keep:
        result = _save(recording)
    publish("record.tick", {"recording": False})
    if on_end is not None:
        on_end(recording.name if keep else None)
    return result


def _save(recording: Recording) -> dict:
    """Write the action: one tape and file, or with checkpoints, one action per part and one that plays them all."""
    events = recording.recorder.tape(recording.screen, device.position())
    length = recording.seconds()
    if events:
        length = min(length, events[-1].t + TAIL)
    edges = [0.0]
    for t in recording.marks:
        if 0 < t < length:
            edges.append(t)
    edges.append(length)
    if len(edges) == 2:
        steps = _write_part(recording, recording.name, events, 0.0, length)
        return {"saved": True, "name": recording.name, "steps": steps}
    calls = []
    for index in range(len(edges) - 1):
        part = f"{recording.name}_{index + 1}"
        _write_part(recording, part, events, edges[index], edges[index + 1])
        calls.append(to_dict(Step("call", {"name": part, "action": True})))
    old_tape = tape.path_for(recording.project / "actions" / f"{recording.name}.py")
    if old_tape.exists():
        old_tape.unlink()  # the parts have the tapes now
    actions_api.save(
        recording.project,
        recording.name,
        [{"name": _title(recording.name), "steps": calls}],
        "Recorded with darbit Studio: its parts in order.",
        timed=True,
    )
    return {"saved": True, "name": recording.name, "steps": len(calls), "parts": len(calls)}


def _write_part(recording: Recording, name: str, events: list, start: float, end: float) -> int:
    """One action and its own tape from `start` to `end` seconds of the recording (its tape starts at 0)."""
    kept = []
    for event in events:
        if start <= event.t < end:
            kept.append(replace(event, t=round(event.t - start, 4)))
    folder = recording.project / "actions"
    folder.mkdir(parents=True, exist_ok=True)
    tape.save(tape.path_for(folder / f"{name}.py"), tape.Tape(kept, recording.window, recording.screen))
    steps = recording.recorder.parts(end - start, start)
    step_dicts = []
    for step in steps:
        step_dicts.append(to_dict(step))
    actions_api.save(
        recording.project,
        name,
        [{"name": _title(name), "steps": step_dicts}],
        "Recorded with darbit Studio.",
        timed=True,
    )
    return len(steps)


def _title(name: str) -> str:
    return name.replace("_", " ").capitalize()


def _current() -> Recording:
    if _recording is None:
        raise ValueError("not recording")
    return _recording


def register() -> None:
    from .app import HANDLERS

    def pause_request(data: dict) -> dict:
        return pause()

    def mark_request(data: dict) -> dict:
        return mark()

    def check_request(data: dict) -> dict:
        return add_check(data)

    def undo_request(data: dict) -> dict:
        return remove_last()

    def stop_request(data: dict) -> dict:
        return stop(bool(data.get("keep", True)))

    def status_request(data: dict) -> dict:
        return status()

    HANDLERS["record.pause"] = pause_request
    HANDLERS["record.mark"] = mark_request
    HANDLERS["record.check"] = check_request
    HANDLERS["record.undo"] = undo_request
    HANDLERS["record.stop"] = stop_request
    HANDLERS["record.status"] = status_request
