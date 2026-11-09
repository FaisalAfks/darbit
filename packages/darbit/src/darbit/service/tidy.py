"""Keeping bots' history small: the service drops each bot's run history, run reports and daily logs older than its
`keep_days` (14 by default) and leaves image looks out of its history, when it starts, when it starts a bot, and
every few hours. See decision 0021."""

import sqlite3
import threading
from datetime import datetime
from pathlib import Path

from ..project.manifest import ProjectError, load
from ..server import history, hub

EVERY = 6 * 3600.0  # seconds between tidies


def tidy(now: datetime | None = None) -> dict[str, dict[str, int]]:
    """Tidy every bot now, each by its own day: what went, by bot name."""
    done = {}
    for found in hub.projects_list({}):
        try:
            project = load(Path(found["path"]))
            done[project.name] = history.tidy(project, now)
        except (ProjectError, OSError, KeyError, sqlite3.Error):
            continue
    return done


class Tidier:
    """Tidies now and every EVERY seconds, until stop()."""

    def __init__(self) -> None:
        self.stopping = threading.Event()

    def start(self) -> None:
        threading.Thread(target=self._run, name="darbit-tidy", daemon=True).start()

    def stop(self) -> None:
        self.stopping.set()

    def _run(self) -> None:
        while not self.stopping.is_set():
            tidy()
            self.stopping.wait(EVERY)
