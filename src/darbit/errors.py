"""Errors. Not finding something is never an error; these are for mistakes and for stopping."""


class DarbitError(Exception):
    """Base for darbit's errors."""


class TargetError(DarbitError):
    """A target can't be used: its image is missing or unreadable, or it has nothing to find or point at."""


class UnknownKey(DarbitError):
    """A key name darbit doesn't know."""


class Stopped(DarbitError):
    """The stop hotkey was pressed."""


class Interrupted(DarbitError):
    """An observer fired. `name` says which; `match` is where its target was seen, if it's an image."""

    def __init__(self, name: str, match: object = None) -> None:
        super().__init__(f"interrupted by {name}")
        self.name = name
        self.match = match
