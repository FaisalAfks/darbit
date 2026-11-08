"""The reader that reads text: darbit's own (core/rapid.py, the `ocr` extra), or one from a plugin.

A plugin package adds a reader under the `darbit.readers` entry point group, and a bot picks it with
`settings.reader = "name"`. The entry point is called with the number of threads to use and gives a Reader
(platform/backend.py): `line(pixels, allowed)` and `lines(pixels, allowed)`.
"""

import warnings
from collections.abc import Callable
from importlib.metadata import entry_points

from ..core import rapid
from ..core.reading import Prepare
from ..platform.backend import Reader
from ..settings import settings
from .log import log

MISSING = 'reading text needs the ocr extra: pip install "darbit[ocr]" (or uv sync --extra ocr in a checkout)'

_made: dict[tuple[str, int], Reader] = {}
_missing: set[str] = set()  # readers whose packages aren't installed, said once


def _factory(name: str) -> Callable[[int], Reader]:
    if name == "rapidocr":
        return rapid.reader
    found = entry_points(group="darbit.readers", name=name)
    if not found:
        raise ValueError(f'no reader called {name!r}: install the plugin that has it, or use "rapidocr"')
    return next(iter(found)).load()


def current() -> Reader | None:
    """The reader settings.reader names, made on first use; None (said once) when its package isn't installed."""
    name = settings.reader
    threads = max(int(settings.read_threads), 1)
    key = (name, threads)
    if key in _made:
        return _made[key]
    if name in _missing:
        return None
    factory = _factory(name)
    try:
        made = factory(threads)
    except ImportError:
        _missing.add(name)
        message = MISSING if name == "rapidocr" else f"the reader {name!r} can't load its packages"
        log(message)
        warnings.warn(message, stacklevel=4)
        return None
    _made[key] = made
    return made


def prepare_for(own: dict | None) -> Prepare:
    """The bot's reading options with a Region's own on top."""
    values = dict(settings.read)
    if own:
        values.update(own)
    return Prepare.from_dict(values)
