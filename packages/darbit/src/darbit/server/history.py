"""A bot's run history in SQLite (.darbit/history.db): every run report line, kept and queried by day and kind.

Bots keep writing their day's run report as before (runtime/log.py), so a bot on any darbit version has a
history. `catch_up` copies the lines added since last time, whole lines only; a report written again from the
start is copied again. The service catches up while it watches a running bot, and before each query.

    history.catch_up(project)
    history.events(project, "2026-10-31", kinds=("gain", "step"))
"""

import json
import sqlite3
from collections.abc import Iterable
from contextlib import closing
from pathlib import Path

from .. import paths
from ..project.manifest import Project
from .dashboard import report_file

DATABASE = "history.db"
SCHEMA = """
create table if not exists reports (file text primary key, day text not null, copied integer not null);
create table if not exists events (
    id integer primary key,
    day text not null,
    time text,
    kind text,
    line text not null
);
create index if not exists events_by_day on events (day, kind);
"""
PREFIX = "report-"
SUFFIX = ".jsonl"


def database(project: Project) -> Path:
    return paths.project_dir(project.folder) / DATABASE


def _open(project: Project) -> sqlite3.Connection:
    path = database(project)
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path, timeout=10)
    connection.executescript(SCHEMA)
    return connection


def reports(project: Project) -> list[Path]:
    """The bot's run reports, oldest first."""
    folder = report_file(project, "x").parent
    if not folder.is_dir():
        return []
    return sorted(folder.glob(f"{PREFIX}*{SUFFIX}"))


def catch_up(project: Project) -> int:
    """Copy the report lines added since last time; how many were added."""
    added = 0
    with closing(_open(project)) as connection, connection:
        for report in reports(project):
            added += _copy(connection, report)
    return added


def _copy(connection: sqlite3.Connection, report: Path) -> int:
    day = report.name[len(PREFIX) : -len(SUFFIX)]
    row = connection.execute("select copied from reports where file = ?", (report.name,)).fetchone()
    copied = row[0] if row else 0
    size = report.stat().st_size
    if size < copied:  # written again from the start
        connection.execute("delete from events where day = ?", (day,))
        copied = 0
    if size == copied:
        return 0
    with report.open("rb") as file:
        file.seek(copied)
        data = file.read(size - copied)
    end = data.rfind(b"\n") + 1  # a line still being written waits for next time
    if end < len(data) and _whole(data[end:]):
        end = len(data)  # the last line has no line break but is whole
    rows = []
    for line in data[:end].splitlines():
        try:
            event = json.loads(line)
        except ValueError:
            continue
        if isinstance(event, dict):
            rows.append((day, str(event.get("time", "")), str(event.get("event", "")), line.decode("utf-8")))
    connection.executemany("insert into events (day, time, kind, line) values (?, ?, ?, ?)", rows)
    connection.execute(
        "insert into reports (file, day, copied) values (?, ?, ?) "
        "on conflict (file) do update set copied = excluded.copied",
        (report.name, day, copied + end),
    )
    return len(rows)


def _whole(line: bytes) -> bool:
    try:
        return isinstance(json.loads(line), dict)
    except ValueError:
        return False


def days(project: Project) -> list[str]:
    """The days with history, newest first."""
    with closing(_open(project)) as connection:
        found = connection.execute("select distinct day from events order by day desc").fetchall()
    return [row[0] for row in found]


def events(project: Project, day: str, kinds: Iterable[str] | None = None) -> list[dict]:
    """A day's events in the order they happened, as the report has them; only `kinds` if given."""
    query = "select line from events where day = ?"
    values: list[str] = [day]
    if kinds is not None:
        chosen = list(kinds)
        query += f" and kind in ({', '.join('?' for _ in chosen)})"
        values.extend(chosen)
    query += " order by id"
    with closing(_open(project)) as connection:
        found = connection.execute(query, values).fetchall()
    return [json.loads(row[0]) for row in found]


def counts(project: Project, day: str) -> dict[str, int]:
    """How many events of each kind a day has."""
    with closing(_open(project)) as connection:
        found = connection.execute(
            "select kind, count(*) from events where day = ? group by kind order by kind", (day,)
        ).fetchall()
    return {kind: count for kind, count in found}


def span(project: Project, day: str) -> tuple[str, str] | None:
    """The first and last event's time on a day ("2026-10-31T09:12:03.120"), or None without events."""
    with closing(_open(project)) as connection:
        first, last = connection.execute(
            "select min(time), max(time) from events where day = ? and time != ''", (day,)
        ).fetchone()
    if first is None:
        return None
    return first, last


def forget_before(project: Project, day: str) -> dict[str, int]:
    """Drop the bot's history, run reports and daily logs from before `day` ("2026-10-02"): what went."""
    gone = {"events": 0, "files": 0}
    with closing(_open(project)) as connection, connection:
        gone["events"] = connection.execute("delete from events where day < ?", (day,)).rowcount
        connection.execute("delete from reports where day < ?", (day,))
    folder = report_file(project, "x").parent
    if not folder.is_dir():
        return gone
    for path in [*folder.glob(f"{PREFIX}*{SUFFIX}"), *folder.glob("????-??-??.log")]:
        dated = path.name[len(PREFIX) : -len(SUFFIX)] if path.name.startswith(PREFIX) else path.stem
        if dated < day:
            try:
                path.unlink()
                gone["files"] += 1
            except OSError:
                continue  # open on Windows (today's, or a reader): next time
    return gone
