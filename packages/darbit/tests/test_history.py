"""A bot's run history in SQLite: report lines copied as they come, whole lines only, and queried by day and kind."""

import json

import pytest

from darbit.project.manifest import load
from darbit.server import history


@pytest.fixture
def project(tmp_path):
    (tmp_path / "darbit.toml").write_text('[bot]\nname = "fish-bot"\n', encoding="utf-8")
    return load(tmp_path)


def report(project, day):
    logs = project.folder / ".darbit" / "logs"
    logs.mkdir(parents=True, exist_ok=True)
    return logs / f"report-{day}.jsonl"


def line(clock, event, **fields):
    return json.dumps({"time": f"2026-10-31T{clock}.000", "event": event, **fields}) + "\n"


def test_lines_are_copied_as_they_come(project):
    path = report(project, "2026-10-31")
    path.write_text(line("09:00:00", "step", step="Fish", state="started"), encoding="utf-8")
    assert history.catch_up(project) == 1
    assert history.catch_up(project) == 0  # nothing new
    with path.open("a", encoding="utf-8") as file:
        file.write(line("09:00:05", "gain", name="Fish", amount=3))
        file.write('{"time": "2026-10-31T09:00:06.000", "ev')  # still being written
    assert history.catch_up(project) == 1
    with path.open("a", encoding="utf-8") as file:
        file.write('ent": "gain", "name": "Fish", "amount": 2}\n')
    assert history.catch_up(project) == 1
    gains = history.events(project, "2026-10-31", kinds=("gain",))
    assert [gain["amount"] for gain in gains] == [3, 2]
    assert history.counts(project, "2026-10-31") == {"gain": 2, "step": 1}
    assert history.span(project, "2026-10-31") == ("2026-10-31T09:00:00.000", "2026-10-31T09:00:06.000")


def test_a_report_written_again_is_copied_again(project):
    path = report(project, "2026-10-31")
    path.write_text(line("09:00:00", "gain", name="Fish", amount=1) * 3, encoding="utf-8")
    history.catch_up(project)
    path.write_text(line("10:00:00", "gain", name="Fish", amount=9), encoding="utf-8")
    history.catch_up(project)
    assert [gain["amount"] for gain in history.events(project, "2026-10-31")] == [9]


def test_days_are_newest_first_and_broken_lines_are_skipped(project):
    report(project, "2026-10-30").write_text(line("09:00:00", "gain", name="Fish", amount=1), encoding="utf-8")
    report(project, "2026-10-31").write_text("not json\n" + line("09:00:00", "step"), encoding="utf-8")
    history.catch_up(project)
    assert history.days(project) == ["2026-10-31", "2026-10-30"]
    assert history.span(project, "2026-11-01") is None


def test_old_days_are_forgotten_and_the_rest_kept(tmp_path, monkeypatch):
    from datetime import datetime

    from darbit.project.manifest import load
    from darbit.server import hub
    from darbit.service import tidy

    folder = tmp_path / "old-bot"
    folder.mkdir()
    (folder / "darbit.toml").write_text('[bot]\nname = "old-bot"\n\n[run]\nkeep_days = 30\n', encoding="utf-8")
    project = load(folder)
    logs = history.report_file(project, "x").parent
    logs.mkdir(parents=True)
    for day in ("2026-09-01", "2026-10-02", "2026-10-31"):
        (logs / f"report-{day}.jsonl").write_text(f'{{"time": "{day}T09:00:00", "event": "gain"}}\n', encoding="utf-8")
        (logs / f"{day}.log").write_text("a line\n", encoding="utf-8")
    history.catch_up(project)
    monkeypatch.setattr(hub, "projects_list", lambda data: [{"path": str(folder)}])
    done = tidy.tidy(datetime(2026, 11, 1, 12))
    assert done["old-bot"] == {"events": 1, "files": 2, "looks": 0, "vacuumed": 0}  # 30 days back is 2 October
    assert history.days(project) == ["2026-10-31", "2026-10-02"]
    assert sorted(path.name for path in logs.iterdir()) == [
        "2026-10-02.log",
        "2026-10-31.log",
        "report-2026-10-02.jsonl",
        "report-2026-10-31.jsonl",
    ]


def test_image_looks_are_left_out(project):
    report(project, "2026-10-31").write_text(
        line("09:00:00", "step", step="Fish", state="started")
        + line("09:00:01", "exists", targets="Rod.png", timeout=0, found=None)
        + line("09:00:02", "wait", targets="Rod.png", timeout=5, found="Rod.png")
        + line("09:00:03", "click", target="Rod.png", done=True),
        encoding="utf-8",
    )
    assert history.catch_up(project) == 2
    assert history.counts(project, "2026-10-31") == {"click": 1, "step": 1}


def test_an_older_history_loses_its_looks_and_shrinks(project):
    import sqlite3
    from contextlib import closing

    path = report(project, "2026-10-31")
    path.write_text(line("09:00:00", "gain", name="Fish", amount=1), encoding="utf-8")
    history.catch_up(project)
    rows = [("2026-10-31", "", "exists", json.dumps({"event": "exists", "pad": "x" * 500}))] * 2000
    with closing(sqlite3.connect(history.database(project))) as connection, connection:
        connection.executemany("insert into events (day, time, kind, line) values (?, ?, ?, ?)", rows)
    before = history.database(project).stat().st_size
    assert history.leave_out_looks(project) == 2000
    assert history.vacuum(project)
    assert history.database(project).stat().st_size < before / 4
    assert history.counts(project, "2026-10-31") == {"gain": 1}
    assert not history.vacuum(project)  # nothing left to give back


def test_vacuum_waits_for_another_connection_then_leaves_it(project, monkeypatch):
    import sqlite3
    from contextlib import closing

    report(project, "2026-10-31").write_text(line("09:00:00", "gain", name="Fish", amount=1), encoding="utf-8")
    history.catch_up(project)
    rows = [("2026-10-31", "", "exists", "x" * 500)] * 2000
    with closing(sqlite3.connect(history.database(project))) as connection, connection:
        connection.executemany("insert into events (day, time, kind, line) values (?, ?, ?, ?)", rows)
    history.leave_out_looks(project)
    monkeypatch.setattr(history, "VACUUM_WAIT", 0.05)
    with closing(sqlite3.connect(history.database(project), isolation_level=None)) as writer:
        writer.execute("begin immediate")  # another process writing
        assert not history.vacuum(project)
        writer.execute("rollback")
    assert history.vacuum(project)  # the next tidy


def test_a_forgotten_day_stays_forgotten_while_its_report_is_still_there(project):
    for day in ("2026-10-01", "2026-10-31"):
        report(project, day).write_text(line("09:00:00", "gain", name="Fish", amount=1), encoding="utf-8")
    history.catch_up(project)
    history.forget_before(project, "2026-10-02")
    # still there, as when a reader held it open and it couldn't be deleted
    report(project, "2026-10-01").write_text(line("09:00:00", "gain", name="Fish", amount=1), encoding="utf-8")
    history.catch_up(project)
    assert history.days(project) == ["2026-10-31"]


def test_the_cutoff_goes_by_the_bots_day(tmp_path):
    from datetime import datetime

    manifest = '[bot]\nname = "late-bot"\n\n[settings]\nday_starts = "03:00"\nkeep_days = 1\n'
    (tmp_path / "darbit.toml").write_text(manifest, encoding="utf-8")
    late = load(tmp_path)
    # 01:00 on the 10th is still the bot's 9th: its today (9th) and yesterday (8th) are kept
    assert history.first_kept(late, datetime(2026, 11, 10, 1, 0)) == "2026-11-08"


def test_keep_days_is_a_setting_and_still_read_from_run(tmp_path):
    from darbit.project.manifest import ProjectError

    def keep_days(tables):
        (tmp_path / "darbit.toml").write_text('[bot]\nname = "a"\n' + tables, encoding="utf-8")
        return load(tmp_path).keep_days

    assert keep_days("") == 14
    assert keep_days("[settings]\nkeep_days = 7\n") == 7
    assert keep_days("[run]\nkeep_days = 30\n") == 30  # where it was before
    assert load(tmp_path).settings["keep_days"] == 30  # so the bot's own darbit keeps 30 too
    for wrong in ("0", "1.5", "true"):
        with pytest.raises(ProjectError):
            keep_days(f"[settings]\nkeep_days = {wrong}\n")
