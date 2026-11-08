"""One bot that sends input at a time (decision 0020): [run] input in darbit.toml, the service refusing a second
input bot or replacing the first, the refusal's shape on the socket and in the CLI, and the soft check for a bot
started without the service. Real bot processes on fakes; no mouse or keys."""

import os
import time
import warnings

import pytest
from test_hub import BOT, bot  # noqa: F401 - the fixture
from test_service import service  # noqa: F401 - the fixture

from darbit import events
from darbit.project.manifest import ProjectError, load
from darbit.server import actions_api, hub, recording_mark
from darbit.service import alongside, client, protocol


def _another(first, name, sends_input=True):
    """A second bot next to `first` in the bots folder."""
    folder = first.parent / name
    folder.mkdir()
    run = "" if sends_input else "\n[run]\ninput = false\n"
    (folder / "darbit.toml").write_text(f'[bot]\nname = "{name}"\nentry = "bot.py"\n{run}', encoding="utf-8")
    (folder / "bot.py").write_text(BOT, encoding="utf-8")
    return folder


@pytest.fixture
def runs(monkeypatch):
    """Bots started in a test are stopped after it, whatever happens."""
    monkeypatch.setattr(hub, "WATCH_EVERY", 0.1)
    yield
    hub.stop_all()


def test_input_is_true_unless_the_bot_says_otherwise(bot):  # noqa: F811
    assert load(bot).input is True
    quiet = _another(bot, "quiet-bot", sends_input=False)
    assert load(quiet).input is False
    (quiet / "darbit.toml").write_text('[bot]\nname = "quiet-bot"\n\n[run]\ninput = "no"\n', encoding="utf-8")
    with pytest.raises(ProjectError, match="input is true or false"):
        load(quiet)


def test_a_second_input_bot_is_refused_naming_the_first(bot, runs):  # noqa: F811
    other = _another(bot, "other-bot")
    assert hub.project_run({"path": str(other)})["status"] == "running"  # alone, it starts
    with pytest.raises(hub.InputBotRunning) as refused:
        hub.project_run({"path": str(bot)})
    assert "other-bot is running" in str(refused.value)
    assert refused.value.code == "input_bot_running"
    assert [(found["name"], found["status"], found["input"]) for found in refused.value.running] == [
        ("other-bot", "running", True)
    ]
    assert hub.status(bot) == "stopped"
    hub.project_pause({"path": str(other)})
    with pytest.raises(hub.InputBotRunning):  # paused still holds the mouse and keys
        hub.project_run({"path": str(bot)})
    hub.project_stop({"path": str(other)})
    assert hub.project_run({"path": str(bot)})["status"] == "running"  # once it stopped, the start goes through


def test_a_bot_without_input_runs_alongside_either_way(bot, runs):  # noqa: F811
    quiet = _another(bot, "quiet-bot", sends_input=False)
    assert hub.project_run({"path": str(bot)})["status"] == "running"
    assert hub.project_run({"path": str(quiet)})["status"] == "running"  # after an input bot
    hub.project_stop({"path": str(bot)})
    assert hub.project_run({"path": str(bot)})["status"] == "running"  # an input bot after it
    running = {found["name"]: found["input"] for found in hub.bots_running({})}
    assert running == {"tick-bot": True, "quiet-bot": False}


def test_replace_stops_the_running_bot_then_starts(bot, runs):  # noqa: F811
    other = _another(bot, "other-bot")
    told = []
    stop_listening = events.listen(lambda topic, data: told.append(data) if topic == "project.status" else None)
    try:
        hub.project_run({"path": str(other)})
        time.sleep(0.5)
        assert hub.project_run({"path": str(bot), "replace": True})["status"] == "running"
        deadline = time.monotonic() + 5
        while time.monotonic() < deadline and not _ends(told, other):
            time.sleep(0.05)
    finally:
        stop_listening()
    assert hub.status(other) == "stopped"
    assert hub.status(bot) == "running"
    assert _ends(told, other) == ["stopped"]  # a replaced bot stopped cleanly: not a failure, no restart


def _ends(told, folder):
    """How the bot's runs ended, from its project.status events."""
    found = []
    for data in told:
        if data["path"] == str(folder) and data["status"] != "running":
            found.append(data["status"])
    return found


def test_a_run_taken_over_from_an_earlier_service_counts(bot, monkeypatch):  # noqa: F811
    other = _another(bot, "other-bot")
    monkeypatch.setattr(hub, "_runs", {})
    control = hub.control_dir(other)
    control.mkdir(parents=True, exist_ok=True)
    try:
        (control / "pid").write_text("999999", encoding="utf-8")  # long gone: not in the way
        assert hub._input_bots_running(bot) == []
        (control / "pid").write_text(str(os.getpid()), encoding="utf-8")  # alive: this test's own process
        with pytest.raises(hub.InputBotRunning, match="other-bot"):
            hub.project_run({"path": str(bot)})
    finally:
        (control / "pid").unlink(missing_ok=True)
        hub._runs.clear()  # never stop this test's own process


def test_a_restart_that_would_collide_is_told_as_a_failure(bot, runs, monkeypatch):  # noqa: F811
    other = _another(bot, "other-bot")
    monkeypatch.setattr(hub, "RESTART_AFTER", 0)
    hub.project_run({"path": str(other)})
    told = []
    stop_listening = events.listen(lambda topic, data: told.append(data) if topic == "project.status" else None)
    try:
        hub._start_again(bot)
    finally:
        stop_listening()
    assert told[-1]["status"] == "failed"
    assert "other-bot is running" in told[-1]["why"]
    assert hub.status(bot) == "stopped"


def test_the_refusal_comes_over_the_socket_with_its_code(service, bot, runs):  # noqa: F811
    _another(bot, "other-bot")
    with client.Client("test") as connection:
        assert connection.call("bot.start", bot="other-bot") == {"status": "running"}
        with pytest.raises(client.ServiceError) as refused:
            connection.call("bot.start", bot="tick-bot")
        assert refused.value.code == "input_bot_running"
        assert [found["name"] for found in refused.value.detail["running"]] == ["other-bot"]
        assert "other-bot is running" in str(refused.value)
        running = connection.call("bots.running")
        assert [(found["name"], found["input"]) for found in running] == [("other-bot", True)]
        assert connection.call("bot.start", bot="tick-bot", replace=True) == {"status": "running"}
        assert connection.call("bot.status", bot="other-bot")["status"] == "stopped"
        with pytest.raises(client.ServiceError) as other_refusal:
            connection.call("bot.start", bot="nobody")
        assert other_refusal.value.code is None  # a plain refusal has no code


def test_a_reply_keeps_its_old_shape_and_new_fields_are_skipped():
    plain = protocol.encode(protocol.Reply(1, error="no bot called x"))
    assert b"code" not in plain and b"detail" not in plain  # what an older client reads
    newer = b'{"type": "reply", "id": 2, "result": 3, "later": "a field from a newer service"}'
    assert protocol.decode(newer) == protocol.Reply(2, 3)


def test_the_cli_names_the_running_bot_and_can_replace_it(service, bot, runs, capsys):  # noqa: F811
    from darbit import cli

    _another(bot, "other-bot")
    assert cli.main(["start", "other-bot"]) == 0
    capsys.readouterr()
    assert cli.main(["start", "tick-bot"]) == 1
    said = capsys.readouterr().out
    assert "other-bot is running and uses the mouse and keys" in said
    assert "darbit start tick-bot --replace" in said
    assert cli.main(["start", "tick-bot", "--replace"]) == 0
    assert capsys.readouterr().out.strip() == "tick-bot: running"
    assert hub.status(bot) == "running"


def test_the_soft_check_runs_only_for_an_input_bot_the_service_didnt_start(bot):  # noqa: F811
    project = load(bot)
    assert alongside.should_check(project, {}) is True
    assert alongside.should_check(None, {}) is False  # not a bot
    assert alongside.should_check(project, {"DARBIT_CONTROL": "x"}) is False  # the service started it
    assert alongside.should_check(project, {"DARBIT_NO_REAL_INPUT": "1"}) is False  # tests
    project.input = False
    assert alongside.should_check(project, {}) is False


def test_the_soft_check_warns_about_an_input_bot_the_service_runs(service, bot, runs):  # noqa: F811
    other = _another(bot, "other-bot")
    project = load(bot)
    assert alongside.check(project) == ""  # nothing running
    hub.project_run({"path": str(other)})
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        said = alongside.check(project)
    assert "other-bot is running through darbit's service" in said
    assert [str(warning.message) for warning in caught] == [said]
    assert alongside.others_running(other) == []  # a bot isn't in its own way


def test_the_soft_check_is_quiet_without_a_service(bot):  # noqa: F811
    assert alongside.others_running(bot) == []


# ---- an action played in the service (#428) and the recorder

FOREVER = "import darbit as d\n\n\n@d.flow\ndef forever():\n    while True:\n        d.sleep(0.01)\n"
STOPS = "import darbit as d\n\n\n@d.flow\ndef stops():\n    d.log('one')\n    d.log('two')\n"


@pytest.fixture
def actions(bot, monkeypatch):  # noqa: F811
    """tick-bot with an action that plays until it's stopped and one with a breakpoint; stopped after the test."""
    folder = bot / "actions"
    folder.mkdir()
    (folder / "__init__.py").write_text("", encoding="utf-8")
    (folder / "forever.py").write_text(FOREVER, encoding="utf-8")
    (folder / "stops.py").write_text(STOPS, encoding="utf-8")
    yield bot
    assert actions_api.stop_playing(5)


def _playing_soon():
    """Whether an action is playing, after a moment to get going."""
    deadline = time.monotonic() + 2
    while time.monotonic() < deadline and actions_api.playing() is None:
        time.sleep(0.02)
    return actions_api.playing() is not None


def test_an_action_is_refused_while_an_input_bot_runs(actions, runs):
    other = _another(actions, "other-bot")
    hub.project_run({"path": str(other)})
    with pytest.raises(hub.InputBotRunning) as refused:
        hub.action_play({"path": str(actions), "name": "forever"})
    assert str(refused.value).startswith("other-bot is running and uses the mouse and keys too")
    assert "or play forever with replace" in str(refused.value)
    assert [found["name"] for found in refused.value.running] == ["other-bot"]
    assert actions_api.playing() is None


def test_an_action_is_refused_while_its_own_bot_runs(actions, runs):
    hub.project_run({"path": str(actions)})
    with pytest.raises(hub.InputBotRunning, match="tick-bot is running"):
        hub.action_play({"path": str(actions), "name": "forever"})


def test_an_action_plays_next_to_a_bot_without_input(actions, runs):
    quiet = _another(actions, "quiet-bot", sends_input=False)
    hub.project_run({"path": str(quiet)})
    assert hub.action_play({"path": str(actions), "name": "forever"}) == {"playing": True}  # the control
    assert _playing_soon()


def test_replace_stops_the_bot_then_plays(actions, runs):
    other = _another(actions, "other-bot")
    told = []
    stop_listening = events.listen(lambda topic, data: told.append(data) if topic == "project.status" else None)
    try:
        hub.project_run({"path": str(other)})
        time.sleep(0.5)
        assert hub.action_play({"path": str(actions), "name": "forever", "replace": True}) == {"playing": True}
        assert _playing_soon()
        deadline = time.monotonic() + 5
        while time.monotonic() < deadline and not _ends(told, other):
            time.sleep(0.05)
    finally:
        stop_listening()
    assert _ends(told, other) == ["stopped"]


def test_a_bot_is_refused_while_an_action_plays(actions, runs):
    other = _another(actions, "other-bot")
    hub.action_play({"path": str(actions), "name": "forever"})
    assert _playing_soon()
    with pytest.raises(hub.InputBotRunning) as refused:
        hub.project_run({"path": str(other)})
    assert "tick-bot's action forever is running" in str(refused.value)
    assert [(found["name"], found["status"], found["action"]) for found in refused.value.running] == [
        ("tick-bot", "playing", "forever")
    ]
    assert hub.status(other) == "stopped"
    quiet = _another(actions, "quiet-bot", sends_input=False)
    assert hub.project_run({"path": str(quiet)})["status"] == "running"  # the control: no input, no refusal


def test_an_action_paused_at_a_line_still_counts_and_replace_stops_it(actions, runs):
    other = _another(actions, "other-bot")
    actions_api.set_breakpoints(actions, "stops", [6])
    hub.action_play({"path": str(actions), "name": "stops"})
    deadline = time.monotonic() + 2
    while time.monotonic() < deadline and actions_api.playing() is None:
        time.sleep(0.02)
    time.sleep(0.2)  # at its breakpoint by now, waiting
    assert actions_api.playing() == (actions, "stops")
    with pytest.raises(hub.InputBotRunning):
        hub.project_run({"path": str(other)})
    assert hub.project_run({"path": str(other), "replace": True})["status"] == "running"
    assert actions_api.playing() is None  # stopped, and done letting go, before the bot started


def test_playing_is_refused_over_the_socket_with_its_code(service, actions, runs):  # noqa: F811
    _another(actions, "other-bot")
    with client.Client("test") as connection:
        connection.call("bot.start", bot="other-bot")
        with pytest.raises(client.ServiceError) as refused:
            connection.call("bot.action.play", bot="tick-bot", name="forever")
        assert refused.value.code == "input_bot_running"
        assert [found["name"] for found in refused.value.detail["running"]] == ["other-bot"]
        assert connection.call("bot.action.play", bot="tick-bot", name="forever", replace=True) == {"playing": True}
        assert connection.call("bot.status", bot="other-bot")["status"] == "stopped"
        with pytest.raises(client.ServiceError) as other_refusal:
            connection.call("bot.start", bot="other-bot")
        assert other_refusal.value.code == "input_bot_running"
        assert other_refusal.value.detail["running"][0]["action"] == "forever"


def test_recording_is_refused_while_an_input_bot_runs(service, bot, runs):  # noqa: F811
    from darbit import worker

    assert alongside.input_bots() == []  # the control: nothing running, nothing in the way
    hub.project_run({"path": str(bot)})
    assert [found["name"] for found in alongside.input_bots()] == ["tick-bot"]
    reply = worker._answer(protocol.Request(1, "record.start", {"path": str(bot), "name": "run"}))
    assert reply.code == "input_bot_running"
    assert reply.error == "tick-bot is running and uses the mouse and keys too: stop it to record run"
    assert [found["name"] for found in reply.detail["running"]] == ["tick-bot"]
    assert worker.record_api._recording is None


# ---- starting during a recording (#431)


@pytest.fixture
def recording(actions, monkeypatch):
    """tick-bot recording actions/run.py in this process, on fake hooks; stopped after the test."""
    from darbit.platform import hooks
    from darbit.server import record_api

    def fake_start(on_event, moves=False):
        return lambda: None

    monkeypatch.setattr(hooks, "start", fake_start)
    monkeypatch.setattr(hooks, "health", lambda restart=False: {})
    monkeypatch.setattr(record_api, "on_end", None)
    record_api.start(actions, "run")
    yield actions
    if record_api._recording is not None:
        record_api.stop(False)


def test_a_bot_is_refused_during_a_recording_even_with_replace(recording, runs):
    other = _another(recording, "other-bot")
    for replace in (False, True):
        with pytest.raises(hub.InputBotRunning) as refused:
            hub.project_run({"path": str(other), "replace": replace})
        said = str(refused.value)
        assert said.startswith("a recording of tick-bot's action run is running")
        assert "finish or cancel the recording to start other-bot (replace doesn't stop a recording)" in said
        assert [(found["name"], found["status"], found["action"]) for found in refused.value.running] == [
            ("tick-bot", "recording", "run")
        ]
    assert hub.status(other) == "stopped"
    assert recording_mark.current() is not None  # the recording goes on
    quiet = _another(recording, "quiet-bot", sends_input=False)
    assert hub.project_run({"path": str(quiet)})["status"] == "running"  # the control: no input, no refusal


def test_an_action_is_refused_during_a_recording_even_with_replace(recording, runs):
    for replace in (False, True):
        with pytest.raises(hub.InputBotRunning, match="finish or cancel the recording to play forever"):
            hub.action_play({"path": str(recording), "name": "forever", "replace": replace})
    assert actions_api.playing() is None


def test_once_the_recording_ends_or_its_worker_is_gone_starts_go_ahead(recording, runs):
    from darbit.server import record_api

    record_api.stop(False)
    assert recording_mark.current() is None
    assert hub.project_run({"path": str(recording)})["status"] == "running"  # the control: nothing in the way
    hub.project_stop({"path": str(recording)})
    recording_mark.write(recording, "run")
    mark = recording_mark._file()
    mark.write_text(mark.read_text(encoding="utf-8").replace(str(os.getpid()), "999999"), encoding="utf-8")
    assert recording_mark.current() is None  # a worker that's gone left it: it counts for nothing
    assert hub.project_run({"path": str(recording)})["status"] == "running"
    recording_mark.clear()


def test_the_recording_refusal_comes_over_the_socket(service, recording, runs):  # noqa: F811
    with client.Client("test") as connection:
        with pytest.raises(client.ServiceError) as refused:
            connection.call("bot.start", bot="tick-bot", replace=True)
        assert refused.value.code == "input_bot_running"
        assert refused.value.detail["running"][0]["status"] == "recording"
        assert connection.call("bot.status", bot="tick-bot")["status"] == "stopped"
