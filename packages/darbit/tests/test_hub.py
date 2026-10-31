"""darbit Studio's requests on a fake bot project: finding bots, running, pausing and stopping a real process,
and the bot's Overview, settings, library and runs. No game, no mouse or keys."""

import json
import sys
import time
from pathlib import Path

import cv2
import numpy as np
import pytest

from darbit import events, paths
from darbit.platform import safety, system
from darbit.server import hub, ui_settings

BOT = """
import darbit as d

with d.step("Loop"):
    while True:
        d.record("tick")
        d.sleep(0.1)
"""


@pytest.fixture
def bot(tmp_path, monkeypatch):
    """A bot installed in a temporary bots folder, with settings, a picture and a report."""

    def bots_dir():
        return tmp_path / "bots"

    def config_dir():
        return tmp_path / "config"

    monkeypatch.setattr(paths, "bots_dir", bots_dir)
    monkeypatch.setattr(paths, "config_dir", config_dir)
    folder = tmp_path / "bots" / "tick-bot"
    (folder / "images").mkdir(parents=True)
    (folder / "darbit.toml").write_text(
        '[bot]\nname = "tick-bot"\nversion = "1.0.0"\nentry = "bot.py"\n', encoding="utf-8"
    )
    (folder / "bot.py").write_text(BOT, encoding="utf-8")
    (folder / "settings.toml").write_text(
        '[speed]\n  [speed.every]\n  type = "int"\n  default = 30\n  min = 1\n', encoding="utf-8"
    )
    picture = np.full((40, 120, 3), 200, np.uint8)
    cv2.imwrite(str(folder / "images" / "Gui.Play.png"), picture)
    return folder


def test_installed_bots_are_listed(bot):
    listed = hub.projects_list({})
    assert listed == [
        {
            "path": str(bot),
            "name": "tick-bot",
            "version": "1.0.0",
            "accent": None,
            "summary": "",
            "installed": True,
            "status": "stopped",
            "since": None,
        }
    ]


def test_a_project_folder_can_be_added(bot, tmp_path):
    other = tmp_path / "dev" / "my-bot"
    other.mkdir(parents=True)
    (other / "darbit.toml").write_text('[bot]\nname = "my-bot"\n', encoding="utf-8")
    added = hub.project_add({"path": str(other)})
    assert added["installed"] is False
    assert [entry["name"] for entry in hub.projects_list({})] == ["tick-bot", "my-bot"]
    with pytest.raises(ValueError, match="no darbit.toml"):
        hub.project_add({"path": str(tmp_path)})


def test_requests_about_unknown_folders_are_refused(bot, tmp_path):
    with pytest.raises(ValueError, match="not a bot darbit Studio knows"):
        hub.dashboard_tiles({"path": str(tmp_path)})


def test_a_bot_runs_pauses_and_stops(bot, monkeypatch):
    monkeypatch.setattr(hub, "WATCH_EVERY", 0.1)
    seen = []

    def remember(topic, data):
        seen.append((topic, data.get("status")))

    stop_listening = events.listen(remember)
    try:
        assert hub.project_run({"path": str(bot)})["status"] == "running"
        with pytest.raises(ValueError, match="already running"):
            hub.project_run({"path": str(bot)})
        assert hub.project_pause({"path": str(bot)})["status"] == "paused"
        assert (hub.control_dir(bot) / "pause").exists()
        assert hub.project_pause({"path": str(bot)})["status"] == "running"
        time.sleep(1.0)  # some ticks reach the report
        started = time.monotonic()
        assert hub.project_stop({"path": str(bot)})["status"] == "stopped"
        assert time.monotonic() - started < hub.STOP_WAIT  # it stopped itself, it wasn't ended
        deadline = time.monotonic() + 5
        while ("project.status", "stopped") not in seen and time.monotonic() < deadline:
            time.sleep(0.05)
    finally:
        stop_listening()
    assert ("project.status", "running") in seen
    assert ("project.status", "stopped") in seen  # a stop the Studio asked for isn't a failure
    assert ("project.changed", None) in seen
    assert hub.status(bot) == "stopped"


def test_the_overview_comes_from_the_report(bot):
    logs = bot / ".darbit" / "logs"
    logs.mkdir(parents=True)
    today = time.strftime("%Y-%m-%d")
    lines = [
        {"time": "10:00:00", "event": "step", "step": "Loop", "state": "started"},
        {"time": "10:00:01", "event": "progress", "label": "Ticks", "done": 3, "total": 10},
    ]
    (logs / f"report-{today}.jsonl").write_text("\n".join(json.dumps(line) for line in lines), encoding="utf-8")
    overview = hub.dashboard_tiles({"path": str(bot)})
    assert overview["project"]["name"] == "tick-bot"
    kinds = [tile["kind"] for tile in overview["tiles"]]
    assert kinds[:3] == ["now", "round", "progress"]
    listed = hub.results_days({"path": str(bot)})
    assert [entry["day"] for entry in listed] == [today]


def test_settings_are_read_and_saved(bot):
    form = hub.settings_get({"path": str(bot)})
    assert form["error"] is None
    assert form["values"] == {"speed.every": 30}
    assert form["sections"][0]["settings"][0]["key"] == "speed.every"
    hub.settings_save({"path": str(bot), "values": {"speed.every": 45}})
    assert hub.settings_get({"path": str(bot)})["values"] == {"speed.every": 45}
    with pytest.raises(ValueError, match="at least 1"):
        hub.settings_save({"path": str(bot), "values": {"speed.every": 0}})


def test_the_library_has_thumbnails_and_scores(bot):
    state = bot / ".darbit" / "state"
    state.mkdir(parents=True)
    (state / "check.jsonl").write_text(json.dumps({"name": "Gui.Play.png", "score": 0.97}) + "\n", encoding="utf-8")
    library = hub.library_list({"path": str(bot)})
    assert library[0]["name"] == "Gui.Play"
    assert library[0]["scores"] == [0.97]
    assert library[0]["kind"] == "image"
    assert library[0]["thumbnail"].startswith("data:image/png;base64,")


def test_the_control_folder_stops_and_pauses(tmp_path, monkeypatch):
    monkeypatch.setattr(safety, "_stopped", __import__("threading").Event())
    monkeypatch.setattr(safety, "_paused", __import__("threading").Event())
    monkeypatch.setattr(safety, "_wake", __import__("threading").Event())
    (tmp_path / "pause").write_text("", encoding="utf-8")
    safety._look_at_control(tmp_path)
    assert safety._paused.is_set()
    (tmp_path / "pause").unlink()
    safety._look_at_control(tmp_path)
    assert not safety._paused.is_set()
    (tmp_path / "stop").write_text("", encoding="utf-8")
    safety._look_at_control(tmp_path)
    assert safety._stopped.is_set()
    assert not (tmp_path / "stop").exists()


def test_ui_settings_stay_in_the_temporary_folder(bot, tmp_path):
    ui_settings.set_value("x", 1)
    assert (tmp_path / "config" / "ui.json").is_file()
    assert Path(sys.executable).exists()


def test_a_bot_with_an_older_darbit_is_ended_at_once(tmp_path, monkeypatch):
    from darbit.platform import input as device

    safety = system.site_packages(tmp_path / ".venv") / "darbit" / "platform" / "safety.py"
    safety.parent.mkdir(parents=True)
    safety.write_text('"""v0.3.0: no control folder."""\n', encoding="utf-8")
    assert not hub.understands_control(tmp_path)
    safety.write_text('CONTROL = "DARBIT_CONTROL"\n', encoding="utf-8")
    assert hub.understands_control(tmp_path)
    assert hub.understands_control(tmp_path / "no-env")  # runs with the Studio's own darbit

    ended = []

    def let_go():
        ended.append("let go")

    def known(data):
        return Path(data["path"])

    monkeypatch.setattr(hub, "end_tree", ended.append)
    monkeypatch.setattr(device, "let_go_of_everything", let_go)
    monkeypatch.setattr(hub, "_folder", known)
    safety.write_text('"""old"""\n', encoding="utf-8")

    class Stubborn:
        pid = 4242

        def poll(self):
            return None

        def wait(self, timeout):
            raise hub.subprocess.TimeoutExpired("bot", timeout)

    (tmp_path / "darbit.toml").write_text('[bot]\nname = "old-bot"\n', encoding="utf-8")
    hub.control_dir(tmp_path).mkdir(parents=True)
    monkeypatch.setitem(hub._runs, str(tmp_path), hub.Run(tmp_path, Stubborn(), 0.0))
    assert hub.project_stop({"path": str(tmp_path)}) == {"status": "stopped"}
    assert ended == [4242, "let go"]  # the whole tree, then every key let go


def test_a_bot_an_earlier_studio_started_is_still_known(tmp_path, monkeypatch):
    import os

    monkeypatch.setattr(hub, "_runs", {})
    control = hub.control_dir(tmp_path)
    control.mkdir(parents=True)
    (control / "pid").write_text("999999", encoding="utf-8")  # long gone
    assert hub.status(tmp_path) == "stopped"
    assert not (control / "pid").exists()
    (control / "pid").write_text(str(os.getpid()), encoding="utf-8")  # alive: this test's own process
    assert hub.status(tmp_path) == "running"
    assert isinstance(hub._runs[str(tmp_path)].process, hub.Earlier)


def test_no_running_bots_to_stop():
    assert hub.running() == []
    hub.stop_all()
