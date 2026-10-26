"""Playing run files. See docs/tasks/T16-player-run-panel.md."""

from pathlib import Path

from .model import Run


def play(run: str | Path | Run, panel: bool = False) -> bool:
    """Play a run: wait for each checkpoint, then its goals' steps. False when a checkpoint doesn't show.
    With panel=True the live run panel opens next to the game."""
    raise NotImplementedError("TODO(T16)")
