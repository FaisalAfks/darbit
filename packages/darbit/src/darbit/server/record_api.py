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
from dataclasses import dataclass, field
from pathlib import Path

from ..platform import hooks
from ..runs.flowfile import Step, statement, to_dict
from ..runs.recorder import RawEvent, Recorder, key_name
from . import actions_api
from .events import publish

TICK = 0.25  # seconds between record.tick events
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
    held: set[str] = field(default_factory=set)  # keys down right now
    hotkey_keys: set[str] = field(default_factory=set)  # keys of a darbit hotkey: their ups are dropped too
    running: threading.Event = field(default_factory=threading.Event)

    def seconds(self) -> float:
        return time.perf_counter() - self.started


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
    t = time_ns / 1e9 - recording.started
    if kind in ("key_down", "key_up"):
        _on_key(recording, kind, key_name(code), t)
    elif kind in ("mouse_down", "mouse_up"):
        if _inside_bar(x, y):
            return
        recording.recorder.add(RawEvent(t, kind, BUTTONS.get(code, "left"), x, y))


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


def start(project: Path, name: str) -> dict:
    """Start recording into actions/<name>.py."""
    global _recording
    if not name.isidentifier():
        raise ValueError(f"{name!r} can't be an action's name: use letters, digits and _")
    if _recording is not None:
        raise ValueError("already recording")
    recording = Recording(project, name)
    _recording = recording
    recording.stop_hooks = hooks.start(_on_event)
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
        "steps": shown,
    }


def _tick(recording: Recording) -> None:
    while recording.running.is_set():
        publish("record.tick", status())
        time.sleep(TICK)


def pause() -> dict:
    recording = _current()
    recording.recorder.paused = not recording.recorder.paused
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
    result: dict = {"saved": False}
    if keep:
        steps = recording.recorder.steps()
        step_dicts = []
        for step in steps:
            step_dicts.append(to_dict(step))
        title = recording.name.replace("_", " ").capitalize()
        actions_api.save(
            recording.project, recording.name, [{"name": title, "steps": step_dicts}], "Recorded with darbit Studio."
        )
        result = {"saved": True, "name": recording.name, "steps": len(steps)}
    publish("record.tick", {"recording": False})
    if on_end is not None:
        on_end(recording.name if keep else None)
    return result


def _current() -> Recording:
    if _recording is None:
        raise ValueError("not recording")
    return _recording


def register() -> None:
    from .app import HANDLERS

    def pause_request(data: dict) -> dict:
        return pause()

    def check_request(data: dict) -> dict:
        return add_check(data)

    def undo_request(data: dict) -> dict:
        return remove_last()

    def stop_request(data: dict) -> dict:
        return stop(bool(data.get("keep", True)))

    def status_request(data: dict) -> dict:
        return status()

    HANDLERS["record.pause"] = pause_request
    HANDLERS["record.check"] = check_request
    HANDLERS["record.undo"] = undo_request
    HANDLERS["record.stop"] = stop_request
    HANDLERS["record.status"] = status_request
