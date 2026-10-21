"""Errors. Not finding something is never an error; these are for mistakes and for stopping."""


class DarbitError(Exception):
    """Base for darbit's errors."""


class TargetError(DarbitError):
    """A target can't be used: its image is missing or unreadable, or it has nothing to find or point at."""


class UnknownKey(DarbitError):
    """A key name darbit doesn't know."""


class Stopped(DarbitError):
    """The stop hotkey was pressed."""
