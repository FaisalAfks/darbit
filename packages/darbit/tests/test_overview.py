"""The Overview as blocks: what a bot shows of its own (d.show, @d.block), the catalog, the author's layout and data."""

import json
from datetime import datetime

import pytest

import darbit as d
from darbit.project.manifest import load
from darbit.runtime import show
from darbit.server import overview


@pytest.fixture
def project(tmp_path):
    (tmp_path / "darbit.toml").write_text('[bot]\nname = "fish-bot"\n', encoding="utf-8")
    return load(tmp_path)


def test_a_bot_shows_values_of_its_own(monkeypatch):
    recorded = []
    monkeypatch.setattr(show.log, "record", lambda event, **fields: recorded.append((event, fields)))
    d.show("Boat", 7, sub="next upgrade at 2 000")
    assert recorded == [("block", {"name": "Boat", "value": 7, "sub": "next upgrade at 2 000"})]
    with pytest.raises(ValueError, match="kind"):
        d.show("Boat", 7, kind="pie")


def test_a_block_function_is_asked_when_due_and_a_failing_one_is_skipped(monkeypatch):
    recorded = []
    monkeypatch.setattr(show.log, "record", lambda event, **fields: recorded.append(fields))
    monkeypatch.setattr(show.log, "log", lambda message: None)
    monkeypatch.setattr(show, "_blocks", [])
    monkeypatch.setattr(show, "_started", True)  # no thread: asked by hand below
    show.block("Bait left", every=60)(lambda: {"value": 12, "unit": "worms"})
    show.block("Broken")(lambda: 1 / 0)
    show.ask_blocks_once(now=100.0)
    show.ask_blocks_once(now=130.0)  # not due yet
    assert recorded == [{"name": "Bait left", "value": 12, "unit": "worms"}]


def events():
    return [
        {"time": "2026-11-02T10:00:00", "event": "step", "step": "Fishing", "state": "started"},
        {"time": "2026-11-02T10:01:00", "event": "progress", "label": "Weekly catch", "done": 72, "total": 100},
        {"time": "2026-11-02T10:02:00", "event": "gain", "name": "Gold", "amount": 40, "total": 900},
        {"time": "2026-11-02T10:03:00", "event": "block", "name": "Boat", "value": 7},
        {"time": "2026-11-02T10:04:00", "event": "block", "name": "Bait", "value": ["worms", "flies"]},
    ]


def test_the_catalog_has_darbits_blocks_then_the_bots(project):
    found = {(block["kind"], block["shows"]): block for block in overview.catalog(project, events(), ["sell"])}
    assert ("ring", "progress:Weekly catch") in found
    assert ("number", "gain:Gold") in found and ("chart", "gain:Gold") in found
    assert found[("number", "block:Boat")]["origin"] == "fish-bot"
    assert ("list", "block:Bait") in found  # a list shown is drawn as a list
    assert found[("button", "action:sell")]["origin"] == "fish-bot"


def test_the_authors_layout_comes_from_overview_toml(project):
    (project.folder / "overview.toml").write_text(
        '[[block]]\nkind = "ring"\nshows = "progress:Weekly catch"\nwidth = 6\n\n[[block]]\nkind = "now"\nwidth = 12\n',
        encoding="utf-8",
    )
    layout = overview.default_layout(project, [])
    assert [(block["kind"], block["shows"], block["width"]) for block in layout] == [
        ("ring", "progress:Weekly catch", 6),
        ("now", "now", 12),
    ]
    (project.folder / "overview.toml").write_text('[[block]]\nkind = "pie"\n', encoding="utf-8")
    with pytest.raises(overview.OverviewError, match="block 1's kind"):
        overview.default_layout(project, [])


def test_without_overview_toml_the_old_tiles_order_it(project):
    blocks = overview.catalog(project, events(), [])
    layout = overview.default_layout(project, blocks)
    assert layout[0]["shows"] == "now"
    assert any(block["shows"] == "progress:Weekly catch" for block in layout)
    assert layout[-1]["kind"] == "recoveries"  # how often it got going again: an all-day bot's health


def test_the_recoveries_block_can_be_placed_in_overview_toml(project):
    shown = [(block["kind"], block["shows"]) for block in overview.catalog(project, [], [])]
    assert ("recoveries", "recoveries") in shown  # on offer before the bot has recovered at all
    (project.folder / "overview.toml").write_text('[[block]]\nkind = "recoveries"\n', encoding="utf-8")
    assert overview.default_layout(project, []) == [
        {"kind": "recoveries", "shows": "recoveries", "title": "recoveries", "width": 4, "origin": "bot"}
    ]


def test_the_data_holds_each_blocks_value(project, tmp_path):
    shot = tmp_path / "logs" / "screenshots"
    shot.mkdir(parents=True)
    (shot / "a.jpg").write_bytes(b"x")
    found = overview.data(project, events(), "2026-11-02", datetime(2026, 11, 2, 11), tmp_path / "logs", ["sell"])
    assert found["progress:Weekly catch"]["done"] == 72
    assert found["gain:Gold"]["today"] == 40 and len(found["gain:Gold"]["week"]) == 7
    assert found["block:Boat"]["value"] == 7
    assert found["action:sell"] == {"name": "sell"}
    assert found["screen"]["picture"].endswith("a.jpg")
    assert json.dumps(found)  # all of it goes over the service as JSON


def test_the_data_counts_todays_recoveries(project, tmp_path):
    recovered = [
        {"time": "2026-11-02T09:00:00", "event": "recovered", "how": "rejoin", "why": "disconnected"},
        {"time": "2026-11-02T10:30:00", "event": "recovered", "how": "back to the menu", "why": "stuck"},
        {"time": "2026-11-02T11:15:00", "event": "recovered", "how": "rejoin", "why": "disconnected"},
        {"time": "2026-11-03T01:00:00", "event": "recovered", "how": "rejoin"},
    ]
    found = overview.data(project, events() + recovered, "2026-11-02", datetime(2026, 11, 3, 2), tmp_path)
    rows = found["recoveries"]
    assert rows["count"] == 4
    assert (rows["reason"], rows["reason_count"]) == ("disconnected", 2)
    assert rows["last"] == {"at": 25 * 3600, "how": "rejoin", "why": "no reason given"}  # past midnight, same day
    assert [(row["how"], row["count"]) for row in rows["hows"]] == [("rejoin", 3), ("back to the menu", 1)]


def test_without_recoveries_the_count_is_none(project, tmp_path):
    rows = overview.data(project, events(), "2026-11-02", datetime(2026, 11, 2, 11), tmp_path)["recoveries"]
    assert rows == {"count": 0, "reason": "", "reason_count": 0, "last": None, "hows": []}


def test_the_week_of_gains_asks_history_for_gains_only(project, monkeypatch):
    asked = []

    def events_of(project, day, kinds=None):
        asked.append(kinds)
        return [{"event": "gain", "name": "Gold", "amount": 5}, {"event": "gain", "name": "Gold", "amount": "x"}]

    monkeypatch.setattr(overview.history, "events", events_of)
    week = overview._week_of_gains(project, "2026-11-09")
    assert week == {"Gold": [5] * 7}
    assert asked == [("gain",)] * 7  # every kind of a week's events is tens of MB of JSON on each refresh
