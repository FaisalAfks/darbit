"""A bot's run history in SQLite (.darbit/history.db): its run report lines, less image looks, by day and kind.

Bots keep writing their day's run report as before (runtime/log.py), so a bot on any darbit version has a
history. `catch_up` copies the lines added since last time, whole lines only, except image looks (LEFT_OUT); a
report written again from the start is copied again. The service catches up while it watches a running bot, and
before each query. `tidy` keeps `keep_days` days and shrinks the file (decision 0021).

    history.catch_up(project)
    history.events(project, "2026-10-31", kinds=("gain", "step"))
"""

import json
import sqlite3
from collections.abc import Iterable
from contextlib import closing
from datetime import datetime
from pathlib import Path

from .. import days as day_names
from .. import paths
from ..project.manifest import Project
from ..runtime.log import REPORT_PREFIX, REPORT_SUFFIX, day_of_file, forget_files_before
from .dashboard import report_file, today

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
create table if not exists forgotten (before text not null);
"""
PREFIX = REPORT_PREFIX
SUFFIX = REPORT_SUFFIX
# image looks: about 90% of a report's lines, read only by the Results page's problems, which take them from the
# day's report instead (results.py); the report keeps every line
LEFT_OUT = ("exists", "wait", "vanish", "find")
VACUUM_WAIT = 1.0  # seconds a VACUUM waits for another connection before it's left for the next tidy


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


def first_kept(project: Project, now: datetime | None = None) -> str:
    """The oldest day of the bot's history kept now, by its own day and `keep_days`."""
    return day_names.first_kept(today(project, now), project.keep_days)


def catch_up(project: Project) -> int:
    """Copy the report lines added since last time; how many were added. A report from a day already forgotten
    (one that couldn't be deleted yet) is left out, so its history doesn't come back."""
    added = 0
    with closing(_open(project)) as connection, connection:
        oldest = _forgotten_before(connection)
        for report in reports(project):
            if day_of_file(report) >= oldest:
                added += _copy(connection, report)
    return added


def _forgotten_before(connection: sqlite3.Connection) -> str:
    """The day history was last forgotten before; "" when it never was."""
    row = connection.execute("select max(before) from forgotten").fetchone()
    return row[0] or ""


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
        if isinstance(event, dict) and event.get("event") not in LEFT_OUT:
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


def tidy(project: Project, now: datetime | None = None) -> dict[str, int]:
    """Keep the bot's last keep_days days and leave image looks out of its history: what went."""
    gone = forget_before(project, first_kept(project, now))
    gone["looks"] = leave_out_looks(project)
    gone["vacuumed"] = int(vacuum(project))
    return gone


def forget_before(project: Project, day: str) -> dict[str, int]:
    """Drop the bot's history, run reports and daily logs from before `day` ("2026-10-02"): what went."""
    gone = {"events": 0, "files": 0}
    with closing(_open(project)) as connection, connection:
        gone["events"] = connection.execute("delete from events where day < ?", (day,)).rowcount
        connection.execute("delete from reports where day < ?", (day,))
        if day > _forgotten_before(connection):
            connection.execute("delete from forgotten")
            connection.execute("insert into forgotten (before) values (?)", (day,))
    # the bot deletes its own reports and logs (runtime/log.py); this is for a bot on an older darbit
    gone["files"] = forget_files_before(report_file(project, "x").parent, day)
    return gone


def leave_out_looks(project: Project) -> int:
    """Delete the image looks a history from before LEFT_OUT still has, a day at a time so no lock is held for long;
    how many went."""
    gone = 0
    marks = ", ".join("?" for _ in LEFT_OUT)
    with closing(_open(project)) as connection:
        found = connection.execute("select distinct day from events").fetchall()
        for (day,) in found:
            with connection:
                gone += connection.execute(
                    f"delete from events where day = ? and kind in ({marks})", (day, *LEFT_OUT)
                ).rowcount
    return gone


def vacuum(project: Project) -> bool:
    """Give the file's free space back once a quarter of it is free (after leave_out_looks, or old days going).
    Waits VACUUM_WAIT at most for other connections; when they're busy it's left for next time. Whether it ran."""
    path = database(project)
    if not path.is_file():
        return False
    with closing(sqlite3.connect(path, timeout=VACUUM_WAIT, isolation_level=None)) as connection:
        try:
            free = connection.execute("pragma freelist_count").fetchone()[0]
            pages = connection.execute("pragma page_count").fetchone()[0]
            if free == 0 or free * 4 < pages:
                return False
            connection.execute("vacuum")
        except sqlite3.OperationalError:
            return False  # another connection is reading or writing: next tidy
    return True
