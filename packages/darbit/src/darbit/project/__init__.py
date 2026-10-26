"""Bot projects: the darbit.toml manifest and a bot's settings schema. See docs/tasks/T17-projects.md, T18."""

from .manifest import Project, find, load

__all__ = ["Project", "find", "load"]
