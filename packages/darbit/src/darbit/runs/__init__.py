"""Run files: recorded runs that a bot plays. See docs/tasks/T14-run-files.md, T15 and T16.

d.play("runs/slime.yaml")
"""

from .model import Checkpoint, Goal, Run, Step, dump, load

__all__ = ["Checkpoint", "Goal", "Run", "Step", "dump", "load"]
