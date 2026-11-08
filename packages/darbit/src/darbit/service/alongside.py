"""A soft check for a bot started without the service (`uv run my-bot`, `darbit run`): the service can't refuse or
even see it, so the bot asks the service, on a thread of its own, whether another bot that uses the mouse and keys
is running, and warns when one is (decision 0020). It never stops the bot and never raises. The input worker asks
the same before it records.
"""

import os
import threading
import warnings
from pathlib import Path

from ..project.manifest import Project
from ..runtime import log

CONTROL = "DARBIT_CONTROL"  # set by the service for a bot it started: that one is already checked
NO_REAL_INPUT = "DARBIT_NO_REAL_INPUT"  # tests: no input, nothing to get in the way of
ASK_WAIT = 2.0  # seconds for the service's answer


def should_check(project: Project | None, environ: dict | None = None) -> bool:
    """Whether this process is a bot that sends input and that the service didn't start."""
    given = os.environ if environ is None else environ
    if project is None or not project.input:
        return False
    return not given.get(CONTROL) and not given.get(NO_REAL_INPUT)


def start(project: Project | None) -> None:
    """Look in the background, so importing darbit never waits for the service."""
    if not should_check(project):
        return
    threading.Thread(target=check, args=(project,), name="darbit-alongside", daemon=True).start()


def check(project: Project) -> str:
    """Warn when the service runs another bot that sends input; the warning, or "" when there's none."""
    others = others_running(project.folder)
    if not others:
        return ""
    names = ", ".join(others)
    message = (
        f"{names} is running through darbit's service and uses the mouse and keys too: the two will get in each "
        f"other's way. Stop one, or start {project.name} with darbit start so the service runs one at a time."
    )
    log.later(message)
    warnings.warn(message, stacklevel=2)
    return message


def others_running(folder: Path) -> list[str]:
    """The names of the other bots the service runs that send input; none when no service answers."""
    found = []
    for bot in input_bots(folder):
        found.append(str(bot.get("name", "")))
    return found


def input_bots(but: Path | None = None) -> list[dict]:
    """The bots the service runs or has paused that send input, as `bots.list` shows them, but `but`; none when no
    service answers."""
    from . import client  # the service's client only when there's something to ask

    try:
        with client.Client("darbit", wait=ASK_WAIT) as service:
            bots = service.call("bots.list")
    except client.ServiceError:
        return []
    if not isinstance(bots, list):
        return []
    found = []
    for bot in bots:
        if bot.get("status") not in ("running", "paused"):
            continue
        if not bot.get("input", True):  # an older service doesn't say: taken to send input
            continue
        if but is not None and _same(str(bot.get("path", "")), but):
            continue
        found.append(bot)
    return found


def _same(path: str, folder: Path) -> bool:
    try:
        return Path(path).resolve() == folder.resolve()
    except OSError:
        return False
