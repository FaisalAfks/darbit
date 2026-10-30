"""Bot projects: the darbit.toml manifest and a bot's settings schema. See docs/archive/tasks/T17-projects.md, T18."""

from .manifest import Project, ProjectError, apply, find, load, setup

__all__ = ["Project", "ProjectError", "apply", "find", "load", "setup"]
