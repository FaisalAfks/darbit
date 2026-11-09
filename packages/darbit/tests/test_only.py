"""Running one mode or one step of a bot (decision 0022): [modes] in darbit.toml, `only` on bot.start reaching the bot
as DARBIT_ONLY, d.only() and d.wants() in the bot, and the service's checks. Real bot processes; no mouse or keys."""

import json
import time

import pytest
from test_hub import BOT, bot  # noqa: F401 - the fixture
from test_service import service  # noqa: F401 - the fixture

import darbit as d
from darbit import events
from darbit.project.manifest import ProjectError, load
from darbit.runtime import show
from darbit.server import hub

MODES = '\n[modes]\nRaid = []\n"Speed Raid" = ["open the list", "pick a character"]\n'

# a bot that does what it's asked, writes it down and ends; a whole round runs until it's stopped
HONOURS = """
import json
import darbit as d

done = []
for mode in ["Raid", "Speed Raid"]:
    if d.wants(mode):
        with d.step(mode):
            for step in ["open the list", "pick a character"]:
                if d.wants(mode, step):
                    done.append(mode + " / " + step)
asked = d.only()
with open("done.json", "w", encoding="utf-8") as file:
    json.dump({"only": str(asked) if asked else None, "done": done}, file)
while not asked:
    d.sleep(0.1)
"""


def _with_modes(folder, code=BOT, run=""):
    (folder / "darbit.toml").write_text(f'[bot]\nname = "tick-bot"\nentry = "bot.py"\n{run}{MODES}', encoding="utf-8")
    (folder / "bot.py").write_text(code, encoding="utf-8")


def _another(first, name):
    folder = first.parent / name
    folder.mkdir()
    (folder / "darbit.toml").write_text(f'[bot]\nname = "{name}"\nentry = "bot.py"\n', encoding="utf-8")
    (folder / "bot.py").write_text(BOT, encoding="utf-8")
    return folder


def _about(topic, data, folder):
    """A change in the bot's status: not another one's from a test before, still ending."""
    return topic == "project.status" and data["path"] == str(folder)


def _wait_for(check, seconds=20.0):
    deadline = time.monotonic() + seconds
    while not check() and time.monotonic() < deadline:
        time.sleep(0.05)
    assert check()


@pytest.fixture
def runs(monkeypatch):
    monkeypatch.setattr(hub, "WATCH_EVERY", 0.1)
    yield
    hub.stop_all()


def test_modes_are_read_in_order_with_their_steps(bot):  # noqa: F811
    assert load(bot).modes == {}
    _with_modes(bot)
    assert load(bot).modes == {"Raid": [], "Speed Raid": ["open the list", "pick a character"]}
    assert hub.describe(bot)["modes"] == [
        {"name": "Raid", "steps": []},
        {"name": "Speed Raid", "steps": ["open the list", "pick a character"]},
    ]
    for wrong in ("Raid = 3", 'Raid = ["", "b"]', "[modes.Raid]\nsteps = 1"):
        (bot / "darbit.toml").write_text(f'[bot]\nname = "tick-bot"\n\n[modes]\n{wrong}\n', encoding="utf-8")
        with pytest.raises(ProjectError, match=r"\[modes\]"):
            load(bot)


def test_only_and_wants_read_what_the_service_asked(monkeypatch):
    monkeypatch.delenv("DARBIT_ONLY", raising=False)
    assert d.only() is None
    assert d.wants("Raid") and d.wants("Raid", "open the list")
    monkeypatch.setenv("DARBIT_ONLY", json.dumps({"mode": "Raid"}))
    assert d.only() == d.Only("Raid") and str(d.only()) == "Raid"
    assert d.wants("Raid") and d.wants("Raid", "any step") and not d.wants("Shop")
    monkeypatch.setenv("DARBIT_ONLY", json.dumps({"mode": "Raid", "step": "open the list"}))
    assert str(d.only()) == "Raid › open the list"
    assert d.wants("Raid") and d.wants("Raid", "open the list")
    assert not d.wants("Raid", "pick a character") and not d.wants("Shop", "open the list")
    monkeypatch.setenv("DARBIT_ONLY", "Raid")
    with pytest.raises(ValueError, match="DARBIT_ONLY"):
        d.only()


def test_a_plan_keeps_only_the_mode_asked_for(monkeypatch):
    planned = []
    monkeypatch.setattr(show.log, "record", lambda event, **fields: planned.append(fields["steps"]))
    monkeypatch.delenv("DARBIT_ONLY", raising=False)
    d.plan(["Raid", "Shop"])
    monkeypatch.setenv("DARBIT_ONLY", json.dumps({"mode": "Shop"}))
    d.plan(["Raid", "Shop"])
    assert planned == [["Raid", "Shop"], ["Shop"]]


@pytest.mark.parametrize(
    ("only", "done", "said"),
    [
        ({"mode": "Speed Raid"}, ["Speed Raid / open the list", "Speed Raid / pick a character"], "Speed Raid"),
        (
            {"mode": "Speed Raid", "step": "pick a character"},
            ["Speed Raid / pick a character"],
            "Speed Raid › pick a character",
        ),
    ],
)
def test_a_start_for_one_mode_or_step_runs_just_that_and_ends_stopped(bot, runs, only, done, said):  # noqa: F811
    _with_modes(bot, HONOURS)
    told = []
    stop_listening = events.listen(lambda topic, data: told.append(data) if _about(topic, data, bot) else None)
    try:
        assert hub.project_run({"path": str(bot), "only": only})["status"] == "running"
        _wait_for(lambda: any(data["status"] != "running" for data in told))
    finally:
        stop_listening()
    assert json.loads((bot / "done.json").read_text(encoding="utf-8")) == {"only": said, "done": done}
    assert [data["status"] for data in told] == ["running", "stopped"]


def test_a_round_never_gets_the_services_own_only(bot, runs, monkeypatch):  # noqa: F811
    _with_modes(bot, HONOURS)
    monkeypatch.setenv("DARBIT_ONLY", json.dumps({"mode": "Raid"}))
    hub.project_run({"path": str(bot)})
    _wait_for(lambda: (bot / "done.json").is_file())
    found = json.loads((bot / "done.json").read_text(encoding="utf-8"))
    assert found["only"] is None and len(found["done"]) == 4
    assert hub.status(bot) == "running"  # a round goes on


def test_the_run_says_what_it_was_started_for_until_it_ends(bot, runs, monkeypatch):  # noqa: F811
    _with_modes(bot)  # one that never ends on its own
    hub.project_run({"path": str(bot), "only": {"mode": "Raid"}})
    assert hub.describe(bot)["only"] == {"mode": "Raid"}
    monkeypatch.setattr(hub, "_runs", {})  # a new service finds it through its control folder
    assert hub.describe(bot)["only"] == {"mode": "Raid"}
    hub.project_stop({"path": str(bot)})
    _wait_for(lambda: not (hub.control_dir(bot) / hub.ONLY_FILE).exists())
    assert hub.describe(bot)["only"] is None


def test_a_mode_or_step_the_bot_doesnt_declare_is_refused_before_anything_stops(bot, runs):  # noqa: F811
    _with_modes(bot)
    other = _another(bot, "other-bot")
    hub.project_run({"path": str(other)})
    asked = [
        ({"mode": "Shop"}, "no mode called Shop"),
        ({"mode": "Raid", "step": "open the list"}, "Raid has no step called open the list"),
        ("Raid", "only names a mode"),
    ]
    for only, said in asked:
        with pytest.raises(ValueError, match=said):
            hub.project_run({"path": str(bot), "only": only, "replace": True})
    assert hub.status(other) == "running"
    assert hub.status(bot) == "stopped"
    with pytest.raises(hub.InputBotRunning):  # one input bot at a time, as for any start
        hub.project_run({"path": str(bot), "only": {"mode": "Raid"}})


def test_a_failed_run_of_one_mode_isnt_started_again(bot, monkeypatch):  # noqa: F811
    _with_modes(bot, "raise SystemExit(3)\n", run="\n[run]\nrestart = 3\n")
    monkeypatch.setattr(hub, "RESTART_AFTER", 0.05)
    monkeypatch.setattr(hub, "WATCH_EVERY", 0.1)
    monkeypatch.setattr(hub, "_restarts", {})
    told = []
    stop_listening = events.listen(lambda topic, data: told.append(data) if _about(topic, data, bot) else None)
    try:
        hub.project_run({"path": str(bot), "only": {"mode": "Raid"}})
        _wait_for(lambda: any(data["status"] == "failed" for data in told))
        time.sleep(0.5)  # a restart would have come by now
    finally:
        stop_listening()
    assert [data["status"] for data in told] == ["running", "failed"]
    assert "restart" not in told[-1]


def test_the_cli_starts_one_mode_or_step(service, bot, runs, capsys):  # noqa: F811
    from darbit import cli

    _with_modes(bot)
    assert cli.main(["start", "tick-bot", "--only", "Speed Raid", "--step", "open the list"]) == 0
    assert hub.describe(bot)["only"] == {"mode": "Speed Raid", "step": "open the list"}
    hub.project_stop({"path": str(bot)})
    capsys.readouterr()
    assert cli.main(["start", "tick-bot", "--only", "Shop"]) == 1
    assert "no mode called Shop" in capsys.readouterr().out
    with pytest.raises(SystemExit):
        cli.main(["start", "tick-bot", "--step", "open the list"])
    _another(bot, "other-bot")
    assert cli.main(["start", "other-bot"]) == 0
    capsys.readouterr()
    assert cli.main(["start", "tick-bot", "--only", "Speed Raid", "--step", "open the list"]) == 1
    said = 'darbit start tick-bot --only "Speed Raid" --step "open the list" --replace'
    assert said in capsys.readouterr().out  # the line to copy keeps the step
