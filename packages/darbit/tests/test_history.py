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
    from datetime import date

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
    done = tidy.tidy(date(2026, 11, 1))
    assert done["old-bot"] == {"events": 1, "files": 2}  # 30 days back from 1 November is 2 October
    assert history.days(project) == ["2026-10-31", "2026-10-02"]
    assert sorted(path.name for path in logs.iterdir()) == [
        "2026-10-02.log",
        "2026-10-31.log",
        "report-2026-10-02.jsonl",
        "report-2026-10-31.jsonl",
    ]
