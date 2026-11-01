"""Keeping bots' history small: the service drops each bot's run history, run reports and daily logs older than its
`[run] keep_days` (30 by default), when it starts and every few hours. See the rebuild plan, section 14."""

import sqlite3
import threading
from datetime import date, timedelta
from pathlib import Path

from ..project.manifest import ProjectError, load
from ..server import history, hub

EVERY = 6 * 3600.0  # seconds between tidies


def tidy(today: date | None = None) -> dict[str, dict[str, int]]:
    """Tidy every bot now: what went, by bot name."""
    today = today or date.today()
    done = {}
    for found in hub.projects_list({}):
        try:
            project = load(Path(found["path"]))
            cutoff = (today - timedelta(days=project.keep_days)).isoformat()
            done[project.name] = history.forget_before(project, cutoff)
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
