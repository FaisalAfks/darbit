"""The run file model: checkpoints, goals, steps and reusable actions. See docs/tasks/T14-run-files.md."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

STEP_KINDS = (
    "press",
    "hold",
    "release",
    "write",
    "wait",
    "click",
    "right_click",
    "move",
    "drag",
    "scroll",
    "turn",
    "until",
    "do",
)


@dataclass
class Step:
    kind: str  # one of STEP_KINDS
    value: Any  # a key, seconds, [x, y] as window fractions, degrees, a target or action name
    note: str = ""
    breakpoint: bool = False


@dataclass
class Goal:
    name: str
    steps: list[Step] = field(default_factory=list)


@dataclass
class Checkpoint:
    name: str
    wait_for: str | None = None  # a target that must be on screen first
    timeout: float = 30
    goals: list[Goal] = field(default_factory=list)


@dataclass
class Run:
    name: str
    window: str | None = None
    checkpoints: list[Checkpoint] = field(default_factory=list)
    actions: dict[str, list[Step]] = field(default_factory=dict)
    version: str = "0.4"


def load(path: str | Path) -> Run:
    """Read and check a run file; errors give the YAML line."""
    raise NotImplementedError("TODO(T14)")


def dump(run: Run, path: str | Path) -> None:
    raise NotImplementedError("TODO(T14)")


def schema() -> dict:
    """The JSON Schema for run files (written to runs/runfile.schema.json)."""
    raise NotImplementedError("TODO(T14)")
