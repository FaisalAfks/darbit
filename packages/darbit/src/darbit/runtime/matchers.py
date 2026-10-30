"""The matcher that finds images: darbit's template matcher (core/matching.py), or one from a plugin.

A plugin package adds a matcher under the `darbit.matchers` entry point group, and a bot picks it with
`settings.matcher = "name"`. A matcher has darbit's `closest(target, haystack, origin, enough, options)` (the best
spot whatever its score) and `every(target, haystack, origin, similarity, limit, options)`.
"""

from importlib.metadata import entry_points
from types import ModuleType

from ..core import matching
from ..core.matching import Options
from ..core.targets import Target
from ..settings import settings

_loaded: dict[str, object] = {"template": matching}


def current() -> ModuleType:
    """The matcher settings.matcher names."""
    name = settings.matcher
    if name not in _loaded:
        found = entry_points(group="darbit.matchers", name=name)
        if not found:
            raise ValueError(f'no matcher called {name!r}: install the plugin that has it, or use "template"')
        _loaded[name] = next(iter(found)).load()
    return _loaded[name]  # type: ignore[return-value]


def options_for(target: Target) -> Options:
    """The bot's matching options with the target's own on top."""
    values = dict(settings.match)
    if target.match:
        values.update(target.match)
    return Options.from_dict(values)
