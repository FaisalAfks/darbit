"""Currencies (decision 0023): a gain's source and step, balances, the Wallet, gains by source and each run's gains."""

from datetime import datetime

import pytest

import darbit as d
from darbit.project.manifest import load
from darbit.runtime import show
from darbit.server import currencies, overview

DAY = "2026-11-10"


@pytest.fixture
def recorded(monkeypatch):
    found = []
    monkeypatch.setattr(show.log, "record", lambda event, **fields: found.append((event, fields)))
    return found


@pytest.fixture
def project(tmp_path):
    (tmp_path / "darbit.toml").write_text('[bot]\nname = "fish-bot"\n', encoding="utf-8")
    return load(tmp_path)


def test_a_gain_keeps_its_source_and_the_step_it_was_recorded_in(recorded, monkeypatch):
    monkeypatch.setattr(d.runtime.steps, "record", lambda *args, **fields: None)
    with d.step("Raid"), d.step("claim"):
        d.record.gain("Gems", 520, source="Raid boss")
        d.record.balance("Gems", 4_990_000, icon="◆")
    d.record.gain("Gems", 5)
    assert recorded == [
        ("gain", {"name": "Gems", "amount": 520, "source": "Raid boss", "step": "Raid > claim"}),
        ("balance", {"name": "Gems", "value": 4_990_000, "icon": "◆", "step": "Raid > claim"}),
        ("gain", {"name": "Gems", "amount": 5}),  # outside every step: it says none
    ]


def test_a_balance_is_a_number(recorded):
    with pytest.raises(TypeError):
        d.record.balance("Gems", "lots")
    with pytest.raises(ValueError):
        d.record.balance("", 4)


def gain(time, name, amount, **fields):
    return {"time": f"{DAY}T{time}", "event": "gain", "name": name, "amount": amount, **fields}


def step(time, name, state):
    return {"time": f"{DAY}T{time}", "event": "step", "step": name, "state": state}


def test_a_gain_counts_under_its_source_its_step_the_open_step_or_other():
    found = currencies.gains_with_sources(
        [
            gain("08:00:00", "Gems", 1),  # outside every step, from an older darbit
            step("09:00:00", "Raid", "started"),
            gain("09:01:00", "Gems", 2),  # an older darbit's gain: the open step
            gain("09:02:00", "Gems", 3, step="Raid > Sakura"),
            gain("09:03:00", "Gems", 4, step="Raid", source="Quests"),
            step("09:04:00", "Raid", "ok"),
        ]
    )
    assert [(one.source, one.run, one.detail) for one in found] == [
        ("other", "", ""),
        ("Raid", "Raid", ""),
        ("Raid", "Raid", "Sakura"),
        ("Quests", "Raid", "Quests"),
    ]


def test_the_wallet_has_each_balance_now_and_todays_change():
    earlier = [{"time": "2026-11-09T20:00:00", "event": "balance", "name": "Tokens", "value": 50, "step": "Lobby"}]
    today = [
        {"time": f"{DAY}T09:00:00", "event": "balance", "name": "Gems", "value": 1000, "icon": "◆", "step": "Lobby"},
        gain("09:10:00", "Gems", 120, total=1120, step="Raid"),
        gain("09:20:00", "Gems", 80, step="Raid"),
        {"time": f"{DAY}T09:41:00", "event": "balance", "name": "Gems", "value": 1200, "step": "Lobby > top"},
        {"time": f"{DAY}T09:00:00", "event": "balance", "name": "Gold", "value": 300, "step": "Lobby"},
        {"time": f"{DAY}T09:30:00", "event": "balance", "name": "Gold", "value": 250, "step": "Lobby"},
    ]
    found = currencies.wallet(earlier, today, DAY)
    rows = {row["name"]: row for row in found["items"]}
    assert (rows["Gems"]["value"], rows["Gems"]["today"], rows["Gems"]["icon"]) == (1200, 200, "◆")  # its gains
    assert rows["Gold"]["today"] == -50  # no gains: since the first read today
    assert (rows["Tokens"]["value"], rows["Tokens"]["today"]) == (50, 0)  # read yesterday
    assert found["read"] == {"at": 9 * 3600 + 41 * 60, "where": "Lobby"}


def test_gains_by_source_keep_one_order_for_today_and_the_week():
    week = [[] for _ in range(6)]
    week[0] = currencies.gains_with_sources([gain("09:00:00", "Gems", 900, step="AFK")])
    week.append(
        currencies.gains_with_sources(
            [
                gain("09:00:00", "Gems", 500, step="Raid"),
                gain("09:10:00", "Gems", 300, step="Speed Raid"),
                gain("09:20:00", "Gold", 7, step="Raid"),
            ]
        )
    )
    found = currencies.by_source("Gems", week)
    assert found["sources"] == ["AFK", "Raid", "Speed Raid"]
    assert found["today"] == [0, 500, 300]
    assert found["week"][0] == [900, 0, 0] and len(found["week"]) == 7


def test_many_sources_keep_the_most_and_count_the_rest_as_other():
    gains = [gain("09:00:00", "Gems", 100 - index, source=f"S{index}") for index in range(9)]
    found = currencies.by_source("Gems", [currencies.gains_with_sources(gains)])
    assert found["sources"] == ["S0", "S1", "S2", "S3", "S4", "other"]
    assert found["today"][-1] == 95 + 94 + 93 + 92


def test_each_run_has_its_gains_and_the_day_a_total_per_source():
    events = [
        step("09:04:00", "Raid", "started"),
        gain("09:10:00", "Gems", 520),  # an older darbit's: the open run's
        gain("09:10:00", "Tokens", 60, step="Raid"),
        step("09:30:00", "Raid", "ok"),
        step("09:31:00", "Speed Raid", "started"),
        gain("09:35:00", "Gems", 180, step="Speed Raid > Sakura"),
        step("09:39:00", "Speed Raid", "ok"),
        step("09:40:00", "Claims", "started"),
        gain("09:41:00", "Gems", 300, step="Claims", source="quests"),
        step("09:42:00", "Claims", "ok"),
        step("09:50:00", "Shop", "started"),  # gave nothing: no line
        step("09:51:00", "Shop", "ok"),
        step("10:04:00", "Raid", "started"),
        gain("10:10:00", "Gems", 540, step="Raid"),
        step("10:11:00", "Raid", "ok"),
        gain("10:12:00", "Gems", 5),  # outside every run
        gain("10:13:00", "Gems", 5),
    ]
    found = currencies.runs(events, DAY)
    assert found["currencies"] == ["Gems", "Tokens"]
    assert [(row["label"], row["gains"]) for row in found["runs"]] == [
        ("Raid", {"Gems": 520, "Tokens": 60}),
        ("Speed Raid · Sakura", {"Gems": 180}),
        ("Claims · quests", {"Gems": 300}),
        ("Raid", {"Gems": 540}),
        ("other", {"Gems": 10}),
    ]
    assert found["runs"][0]["start"] == 9 * 3600 + 4 * 60
    assert [(row["source"], row["runs"], row["gains"]) for row in found["by_source"]] == [
        ("Raid", 2, {"Gems": 1060, "Tokens": 60}),
        ("quests", 1, {"Gems": 300}),
        ("Speed Raid", 1, {"Gems": 180}),
        ("other", 1, {"Gems": 10}),
    ]


def test_the_wallet_and_gains_by_source_are_offered_but_not_placed(project, tmp_path):
    events = [
        step("09:00:00", "Raid", "started"),
        gain("09:01:00", "Gems", 40, step="Raid"),
        {"time": f"{DAY}T09:02:00", "event": "balance", "name": "Gems", "value": 900, "step": "Raid"},
    ]
    blocks = overview.catalog(project, events, [])
    shown = {(block["kind"], block["shows"]) for block in blocks}
    assert ("wallet", "wallet") in shown and ("sources", "sources:Gems") in shown
    layout = overview.default_layout(project, blocks)
    assert [block for block in layout if block["kind"] in ("wallet", "sources")] == []
    data = overview.data(project, events, DAY, datetime(2026, 11, 10, 10), tmp_path)
    assert data["wallet"]["items"][0]["value"] == 900
    assert data["sources:Gems"]["sources"] == ["Raid"] and data["sources:Gems"]["names"] == ["Gems"]
    assert data["sources:Gems"]["today"] == [40]


def test_an_overview_toml_can_place_the_wallet_and_gains_by_source(project):
    (project.folder / "overview.toml").write_text(
        '[[block]]\nkind = "wallet"\nwidth = 6\n\n[[block]]\nkind = "sources"\nshows = "sources:Gems"\nwidth = 6\n',
        encoding="utf-8",
    )
    layout = overview.default_layout(project, [])
    assert [(block["kind"], block["shows"]) for block in layout] == [("wallet", "wallet"), ("sources", "sources:Gems")]
