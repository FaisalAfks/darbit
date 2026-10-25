"""The recorder: keyboard and mouse events into run-file steps. See docs/tasks/T15-recorder.md.

The hooks (platform/hooks.py) only queue raw events; everything here is pure, so it's tested with
lists of fake events.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .model import Checkpoint, Run, Step

PRESS_MAX = 0.15  # down and up within this many seconds is a press, longer is hold ... release
MERGE_GAP = 0.03  # gaps shorter than this aren't a wait
WAIT_STEP = 0.05  # waits are rounded to this


@dataclass(frozen=True)
class RawEvent:
    t: float  # seconds since the recording started
    kind: str  # "key_down", "key_up", "mouse_down", "mouse_up", "mouse_move", "wheel"
    key: str = ""  # key or button name
    x: int = 0
    y: int = 0


@dataclass
class Recorder:
    name: str
    window: str | None = None
    events: list[RawEvent] = field(default_factory=list)
    marks: list[tuple[float, Checkpoint]] = field(default_factory=list)
    paused: bool = False

    def add(self, event: RawEvent) -> None:
        if not self.paused:
            self.events.append(event)

    def mark(self, t: float, checkpoint: Checkpoint) -> None:
        self.marks.append((t, checkpoint))

    def steps(self, events: list[RawEvent]) -> list[Step]:
        """Presses, holds, waits, turns, clicks and drags from raw events."""
        raise NotImplementedError("TODO(T15)")

    def run(self) -> Run:
        """The whole recording as a run: one checkpoint per mark, steps between marks in its goal."""
        raise NotImplementedError("TODO(T15)")
