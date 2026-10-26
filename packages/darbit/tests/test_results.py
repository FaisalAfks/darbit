"""The Results page from a bot's run report: gains (today, the week, total), problems grouped, the timeline,
and the calls bots use to report them: d.record.gain and d.plan."""

import json

import pytest

import darbit as d
from darbit.project.manifest import load
from darbit.server import results


@pytest.fixture
def project(tmp_path):
    (tmp_path / "darbit.toml").write_text('[bot]\nname = "fish-bot"\n', encoding="utf-8")
    return load(tmp_path)


def write_day(project, day, lines):
    logs = project.folder / ".darbit" / "logs"
    logs.mkdir(parents=True, exist_ok=True)
    text = "\n".join(json.dumps(line) for line in lines)
    (logs / f"report-{day}.jsonl").write_text(text, encoding="utf-8")


def at(day, clock):
    return f"{day}T{clock}.000"


def test_a_day_has_its_gains_week_and_total(project):
    write_day(
        project, "2026-10-24", [{"time": at("2026-10-24", "09:00:00"), "event": "gain", "name": "Fish", "amount": 30}]
    )
    write_day(
        project,
        "2026-10-26",
        [
            {
                "time": at("2026-10-26", "09:00:00"),
                "event": "gain",
                "name": "Fish",
                "amount": 3,
                "total": 100,
                "icon": "🐟",
            },
            {"time": at("2026-10-26", "09:30:00"), "event": "gain", "name": "Coins", "amount": 50},
            {"time": at("2026-10-26", "10:00:00"), "event": "gain", "name": "Fish", "amount": 2, "total": 102},
        ],
    )
    page = results.day(project, "2026-10-26")
    fish = page["gains"][0]
    assert fish["name"] == "Fish"  # the first one recorded leads
    assert fish["today"] == 5
    assert fish["total"] == 102
    assert fish["icon"] == "🐟"
    assert fish["week"] == [0, 0, 0, 0, 30, 0, 5]
    assert page["week_days"][-1] == "2026-10-26"
    assert page["start"] == 9 * 3600
    assert page["end"] == 10 * 3600


def test_problems_are_grouped_and_time_lost_is_counted(project):
    day = "2026-10-23"
    lines = []
    for clock in ("12:58:00", "13:20:00", "13:41:00"):
        lines.append({"time": at(day, clock), "event": "step", "step": "Speed Raid", "state": "started"})
        lines.append(
            {
                "time": at(day, clock),
                "event": "step",
                "step": "Speed Raid > Leave",
                "state": "failed",
                "reason": "not found",
            }
        )
        lines.append(
            {
                "time": at(day, clock),
                "event": "step",
                "step": "Speed Raid",
                "state": "failed",
                "seconds": 600,
                "reason": "not found",
            }
        )
    lines.append({"time": at(day, "15:00:00"), "event": "step", "step": "Raid", "state": "started"})
    lines.append({"time": at(day, "15:40:00"), "event": "step", "step": "Raid", "state": "ok", "seconds": 2400})
    write_day(project, day, lines)
    page = results.day(project, day)
    assert page["finished"] == {"done": 1, "total": 4}
    assert page["lost_seconds"] == 1800
    leave = page["problems"][0]
    assert (leave["step"], leave["reason"], leave["count"]) in (
        ("Leave", "not found", 3),
        ("Speed Raid", "not found", 3),
    )
    lanes = {lane["name"]: lane["blocks"] for lane in page["lanes"]}
    assert len(lanes["Speed Raid"]) == 3
    assert lanes["Raid"][0]["state"] == "ok"
    assert lanes["Raid"][0]["start"] == 15 * 3600


def test_the_day_list_has_the_lead_gain(project):
    write_day(
        project, "2026-10-25", [{"time": at("2026-10-25", "08:00:00"), "event": "gain", "name": "Gems", "amount": 10}]
    )
    write_day(
        project,
        "2026-10-26",
        [
            {"time": at("2026-10-26", "08:00:00"), "event": "gain", "name": "Gems", "amount": 640},
            {"time": at("2026-10-26", "12:00:00"), "event": "step", "step": "Raid", "state": "failed"},
        ],
    )
    listed = results.days(project)
    assert [entry["day"] for entry in listed] == ["2026-10-26", "2026-10-25"]
    assert listed[0]["lead"] == {"name": "Gems", "amount": 640, "icon": None}
    assert listed[0]["seconds"] == 4 * 3600
    assert listed[0]["problems"] == 1


@pytest.mark.parametrize(
    ("time", "seconds"),
    [
        ("2026-10-26T10:04:31.500", 36271.5),
        ("10:04:31", 36271),
        ("10:04", 36240),
        ("", None),
        (None, None),
        ("x:y", None),
    ],
)
def test_report_times_become_seconds(time, seconds):
    assert results.seconds_of(time) == seconds


def test_gain_and_plan_go_to_the_report(monkeypatch):
    seen = []

    def record(event, **fields):
        seen.append((event, fields))

    monkeypatch.setattr(d.runtime.log, "record", record)
    d.record.gain("Gems", 120, total=48210, icon="◆")
    d.record.gain("Chests", 1)
    d.plan(["Raid", "AFK"])
    d.record("speed raid done", character="Sakura")
    assert seen == [
        ("gain", {"name": "Gems", "amount": 120, "total": 48210, "icon": "◆"}),
        ("gain", {"name": "Chests", "amount": 1}),
        ("plan", {"steps": ["Raid", "AFK"]}),
        ("speed raid done", {"character": "Sakura"}),
    ]
    with pytest.raises(ValueError):
        d.record.gain("", 1)
    with pytest.raises(TypeError):
        d.record.gain("Gems", "lots")
    with pytest.raises(ValueError):
        d.plan(["Raid", ""])
