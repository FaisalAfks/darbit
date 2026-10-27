"""Named steps for the run report.

    with d.step("Speed Raid"):
        with d.step("pick a character"):
            ...

Each step records when it started, how long it took and how it ended: ok, failed
(with the reason and a screenshot), interrupted (by which observer) or stopped.
Steps inside steps are recorded with their path, e.g. "Speed Raid > pick a character".
Bots can add their own events with d.record("speed raid done", character="Naruto").
"""

import threading
import time
from collections.abc import Iterator
from contextlib import contextmanager

from ..errors import Interrupted, Stopped
from .log import log, record, screenshot

_stack = threading.local()


def _path() -> list[str]:
    if not hasattr(_stack, "names"):
        _stack.names = []
    return _stack.names


@contextmanager
def step(name: str) -> Iterator[None]:
    """A named part of a run; see the module's description."""
    path = _path()
    path.append(name)
    where = " > ".join(path)
    started = time.monotonic()
    record("step", step=where, state="started")

    def end(outcome: str, **fields: object) -> None:
        record("step", step=where, state=outcome, seconds=round(time.monotonic() - started, 2), **fields)

    try:
        yield
    except Stopped:
        end("stopped")
        raise
    except Interrupted as event:
        end("interrupted", reason=event.name)
        raise
    except Exception as error:
        shot = screenshot(f"failed_{name}")
        end("failed", reason=str(error) or type(error).__name__, screenshot=shot)
        log(f"step {where} failed: {error}")
        raise
    else:
        end("ok")
    finally:
        path.pop()


def flow(function):
    """Mark a function as an action (decision 0010): the Studio opens it as steps, and calling it plays it."""
    function.darbit_flow = True
    return function
