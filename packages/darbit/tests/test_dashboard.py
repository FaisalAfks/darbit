"""A bot's Overview tiles from its run report (decision 0011): d.progress, d.next, [studio], and every tile."""

import json
from datetime import datetime, timedelta

import pytest

import darbit as d
from darbit.project.manifest import ProjectError, load
from darbit.runtime import show
from darbit.server import dashboard

TODAY = "2026-10-26"
NOON = datetime(2026, 10, 26, 12, 0, 0)


def project_with(tmp_path, events: list[dict], manifest: str = '[bot]\nname = "test-bot"\n'):
    (tmp_path / "darbit.toml").write_text(manifest, encoding="utf-8")
    logs = tmp_path / ".darbit" / "logs"
    logs.mkdir(parents=True)
    lines = []
    for event in events:
        lines.append(json.dumps(event))
    (logs / f"report-{TODAY}.jsonl").write_text("\n".join(lines) + "\nnot json\n", encoding="utf-8")
    return load(tmp_path)


def by_kind(tiles) -> dict:
    found = {}
    for tile in tiles:
        found[tile.kind] = tile
    return found


EVENTS = [
    {"time": "10:20:00", "event": "step", "step": "Boss Rush", "state": "started"},
    {"time": "10:26:00", "event": "step", "step": "Boss Rush", "state": "ok", "seconds": 360},
    {"time": "11:00:00", "event": "step", "step": "AFK", "state": "started"},
    {
        "time": "11:01:00",
        "event": "step",
        "step": "AFK",
        "state": "failed",
        "seconds": 60,
        "reason": "no rewards",
        "screenshot": "afk.jpg",
    },
    {"time": "11:24:00", "event": "step", "step": "Speed Raid", "state": "started"},
    {"time": "11:24:05", "event": "step", "step": "Speed Raid > Sakura", "state": "started"},
    {"time": "11:24:30", "event": "step", "step": "Speed Raid > Sakura > Pick", "state": "started"},
    {"time": "11:24:40", "event": "step", "step": "Speed Raid > Sakura > Pick", "state": "ok", "seconds": 10},
    {"time": "11:24:41", "event": "step", "step": "Speed Raid > Sakura > Fight", "state": "started"},
    {"time": "11:24:42", "event": "exists", "targets": "Dim.Game.Left", "found": "Dim.Game.Left"},
    {"time": "11:00:10", "event": "observer", "name": "Disconnected", "state": "watching"},
    {"time": "11:00:10", "event": "observer", "name": "Roblox closed", "state": "watching"},
    {"time": "08:41:00", "event": "observer", "name": "Roblox closed", "state": "fired"},
    {"time": "11:23:40", "event": "speed raid done", "character": "Natsu", "done": 31},
    {"time": "11:23:41", "event": "progress", "label": "Speed Raid this week", "done": 31, "total": 133},
    {"time": "11:25:00", "event": "progress", "label": "Speed Raid this week", "done": 32, "total": 133},
    {"time": "11:25:01", "event": "progress", "label": "Boss Rush today", "done": 1, "total": 1},
    {"time": "11:00:00", "event": "next", "label": "Raid hour", "at": "2026-10-26T12:00:00"},
    {"time": "11:00:00", "event": "next", "label": "Old", "at": "2026-10-26T09:00:00"},
    {"time": "11:00:00", "event": "next", "label": "Weekly reset", "at": "2026-10-27T07:00:00"},
]


def test_every_tile_from_a_report(tmp_path):
    tiles = by_kind(dashboard.tiles(project_with(tmp_path, EVENTS), TODAY, NOON))
    assert tiles["now"].data == {"path": ["Speed Raid", "Sakura", "Fight"], "since": "11:24:41"}
    steps = tiles["round"].data["steps"]
    assert [row["name"] for row in steps] == ["Boss Rush", "AFK", "Speed Raid"]
    assert steps[0]["state"] == "ok" and steps[1]["reason"] == "no rewards" and steps[2]["state"] == "running"
    assert tiles["progress"].data["items"] == [
        {"label": "Speed Raid this week", "done": 32, "total": 133},
        {"label": "Boss Rush today", "done": 1, "total": 1},
    ]
    upcoming = tiles["next"].data["items"]
    assert [item["label"] for item in upcoming] == ["Raid hour", "Weekly reset"]  # the past one is gone
    assert upcoming[0]["in_seconds"] == 0
    activity = tiles["activity"].data["items"]
    assert [item["event"] for item in activity] == ["speed raid done"]  # darbit's own detail is left out
    assert activity[0]["fields"] == {"character": "Natsu", "done": 31}
    assert tiles["failures"].data["items"][0] == {
        "time": "11:01:00",
        "step": "AFK",
        "reason": "no rewards",
        "screenshot": "afk.jpg",
    }
    watching = tiles["watching"].data["items"]
    assert watching[1] == {"name": "Roblox closed", "state": "watching", "fired": 1, "last_fired": "08:41:00"}


def test_a_quiet_day_shows_only_now(tmp_path):
    tiles = dashboard.tiles(project_with(tmp_path, []), TODAY, NOON)
    assert [tile.kind for tile in tiles] == ["now"]
    assert tiles[0].data == {"path": [], "since": None}


def test_studio_table_picks_and_orders_tiles(tmp_path):
    manifest = (
        '[bot]\nname = "test-bot"\n[studio]\nsummary = "Raids all day"\ntiles = ["progress:Boss Rush today", "now"]\n'
    )
    project = project_with(tmp_path, EVENTS, manifest)
    assert project.summary == "Raids all day"
    tiles = dashboard.tiles(project, TODAY, NOON)
    assert [tile.kind for tile in tiles] == ["progress", "now"]
    assert tiles[0].title == "Boss Rush today"
    assert tiles[0].data["items"] == [{"label": "Boss Rush today", "done": 1, "total": 1}]


def test_an_unknown_tile_is_an_error(tmp_path):
    with pytest.raises(ProjectError, match="unknown tile 'charts'"):
        project_with(tmp_path, [], '[bot]\nname = "x"\n[studio]\ntiles = ["now", "charts"]\n')


def test_setup_counts_the_guides_pictures(tmp_path):
    project = project_with(tmp_path, [], '[bot]\nname = "x"\n[images]\nfolders = ["assets/images"]\n')
    (tmp_path / "guide.toml").write_text(
        'title = "x"\n[[screen]]\nname = "Lobby"\n  [[screen.take]]\n  image = "Gui.Play"\n  say = "Play"\n'
        '  [[screen.take]]\n  image = "Gui.Bag"\n',
        encoding="utf-8",
    )
    (tmp_path / "assets" / "images").mkdir(parents=True)
    (tmp_path / "assets" / "images" / "Gui.Play.png").write_bytes(b"")
    setup = by_kind(dashboard.tiles(project, TODAY, NOON))["setup"]
    assert setup.data == {"done": 1, "total": 2, "current": {"name": "Gui.Bag", "screen": "Lobby", "say": ""}}


def test_a_bots_calls_end_up_in_the_tiles(tmp_path, monkeypatch):
    (tmp_path / "darbit.toml").write_text('[bot]\nname = "test-bot"\n', encoding="utf-8")
    monkeypatch.setattr(d.settings, "logs", tmp_path / ".darbit" / "logs")
    monkeypatch.setattr(d.settings, "log", True)
    with d.step("Speed Raid"):
        d.progress("Speed Raid this week", 5, 133)
        d.next("Weekly reset", datetime.now() + timedelta(days=2))
        d.record("speed raid done", character="Naruto")
        with d.step("Naruto"):
            tiles = by_kind(dashboard.tiles(load(tmp_path)))
    assert tiles["now"].data["path"] == ["Speed Raid", "Naruto"]
    assert tiles["progress"].data["items"] == [{"label": "Speed Raid this week", "done": 5, "total": 133}]
    assert tiles["next"].data["items"][0]["label"] == "Weekly reset"
    assert tiles["activity"].data["items"][0]["fields"] == {"character": "Naruto"}


@pytest.mark.parametrize(
    ("call", "message"),
    [
        (lambda: show.progress("", 1, 2), "needs a label"),
        (lambda: show.progress("x", 1, 0), "more than 0"),
        (lambda: show.progress("x", 3, 2), "from 0 to 2"),
        (lambda: show.next_up("x", "tomorrow"), "datetime"),
    ],
)
def test_mistakes_in_the_calls_say_what_is_wrong(call, message, monkeypatch):
    monkeypatch.setattr(d.settings, "log", False)
    with pytest.raises((ValueError, TypeError), match=message):
        call()


def test_the_plan_shows_steps_still_to_come_and_gains_add_up(tmp_path):
    events = [
        {"time": "09:00:00", "event": "plan", "steps": ["Raid", "Speed Raid", "AFK"]},
        {"time": "09:01:00", "event": "step", "step": "Speed Raid", "state": "started"},
        {"time": "09:02:00", "event": "gain", "name": "Gems", "amount": 100, "total": 900, "icon": "◆"},
        {"time": "09:03:00", "event": "gain", "name": "Gems", "amount": 20, "total": 920},
        {"time": "09:04:00", "event": "gain", "name": "Gold", "amount": "lots"},
    ]
    tiles = by_kind(dashboard.tiles(project_with(tmp_path, events), TODAY, NOON))
    steps = tiles["round"].data["steps"]
    assert [(row["name"], row["state"]) for row in steps] == [
        ("Raid", "planned"),
        ("Speed Raid", "running"),
        ("AFK", "planned"),
    ]
    assert tiles["gains"].data["items"] == [{"name": "Gems", "today": 120, "total": 920, "icon": "◆"}]
    assert "activity" not in tiles  # gains and plans are darbit's own detail


def test_a_growing_report_is_read_a_bit_at_a_time(tmp_path):
    from darbit.server import dashboard as board

    report = tmp_path / "report.jsonl"
    report.write_text('{"event": "a"}\n{"event": "b"}\n{"event": "c', encoding="utf-8")  # the last line isn't done
    assert [event["event"] for event in board.read_events(report)] == ["a", "b"]
    with report.open("a", encoding="utf-8") as file:
        file.write('"}\nnot json\n{"event": "d"}\n')
    assert [event["event"] for event in board.read_events(report)] == ["a", "b", "c", "d"]
    report.write_text('{"event": "new day"}\n', encoding="utf-8")  # shorter: started again
    assert [event["event"] for event in board.read_events(report)] == ["new day"]
