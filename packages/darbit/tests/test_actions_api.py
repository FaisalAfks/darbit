"""Actions in the Studio: listing, reading and saving files, breakpoints, and playing with a line-by-line trace.
The actions here only log and sleep, so nothing touches the mouse or keyboard."""

import threading
import time

import pytest

from darbit import events, paths
from darbit.server import actions_api

COUNT = """import darbit as d
from .helper import helper


@d.flow
def count():
    with d.step("Count"):
        d.log("one")
        d.log("two")
        helper()
        d.log("three")
"""

HELPER = """import darbit as d


@d.flow
def helper():
    d.log("helping")
"""

FOREVER = """import darbit as d


@d.flow
def forever():
    while True:
        d.sleep(0.01)
"""


@pytest.fixture
def project(tmp_path, monkeypatch):
    def project_dir(folder):
        return folder / ".darbit"

    monkeypatch.setattr(paths, "project_dir", project_dir)
    (tmp_path / "darbit.toml").write_text('[bot]\nname = "test-bot"\n', encoding="utf-8")
    actions = tmp_path / "actions"
    actions.mkdir()
    (actions / "__init__.py").write_text("", encoding="utf-8")
    (actions / "count.py").write_text(COUNT, encoding="utf-8")
    (actions / "helper.py").write_text(HELPER, encoding="utf-8")
    (actions / "forever.py").write_text(FOREVER, encoding="utf-8")
    (actions / "broken.py").write_text("x = (\n", encoding="utf-8")
    return tmp_path


def test_actions_are_listed_with_who_uses_them(project):
    listed = {}
    for entry in actions_api.listing(project):
        listed[entry["name"]] = entry
    assert listed["count"]["steps"] == 4
    assert listed["helper"]["used_by"] == ["count"]
    assert "error" in listed["broken"]


def test_read_and_save_round_trip(project):
    action = actions_api.read(project, "count")
    assert action["calls"] == ["helper"]
    assert action["sections"][0]["name"] == "Count"
    action["sections"][0]["steps"].insert(0, {"kind": "wait", "args": {"seconds": 0.5}})
    saved = actions_api.save(project, "count", action["sections"])
    assert saved["sections"][0]["steps"][0]["args"] == {"seconds": 0.5}
    text = (project / "actions" / "count.py").read_text(encoding="utf-8")
    assert "        d.sleep(0.5)\n" in text
    assert "from .helper import helper" in text
    with pytest.raises(ValueError):
        actions_api.save(project, "not a name", [])


def test_breakpoints_stay_out_of_the_file(project):
    actions_api.set_breakpoints(project, "count", [9, 8, 9])
    assert actions_api.read(project, "count")["breakpoints"] == [8, 9]
    assert "breakpoint" not in (project / "actions" / "count.py").read_text(encoding="utf-8")


def wait_for(seen, topic, timeout=5.0):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        for event in seen:
            if event[0] == topic:
                return event
        time.sleep(0.02)
    raise AssertionError(f"no {topic} in {seen}")


def test_play_follows_lines_and_stops_at_breakpoints(project):
    seen = []
    lock = threading.Lock()

    def remember(topic, data):
        if topic.startswith("action."):
            with lock:
                seen.append((topic, data))

    stop_listening = events.listen(remember)
    try:
        actions_api.set_breakpoints(project, "count", [10])  # helper()
        actions_api.play(project, "count")
        paused = wait_for(seen, "action.paused")
        assert paused[1] == {"action": "count", "line": 10}
        actions_api.control("step")  # into the helper
        time.sleep(0.2)
        actions_api.control("resume")
        ended = wait_for(seen, "action.ended")
    finally:
        stop_listening()
    assert ended[1]["status"] == "done"
    lines = []
    for topic, data in seen:
        if topic == "action.line":
            lines.append((data["action"], data["line"]))
    assert ("count", 8) in lines
    assert ("helper", 6) in lines  # the trace follows into the called action


def test_play_can_be_stopped(project):
    seen = []
    stop_listening = events.listen(lambda topic, data: seen.append((topic, data)))
    try:
        actions_api.play(project, "forever")
        time.sleep(0.2)
        actions_api.control("stop")
        ended = wait_for(seen, "action.ended")
    finally:
        stop_listening()
    assert ended[1]["status"] == "stopped"


def test_renaming_an_action_follows_it_everywhere(project):
    actions_api.set_breakpoints(project, "helper", [6])
    (project / "actions" / "helper.tape.json").write_text("{}", encoding="utf-8")
    renamed = actions_api.rename(project, "helper", "go_to_boss")
    assert renamed["name"] == "go_to_boss"
    folder = project / "actions"
    assert not (folder / "helper.py").exists()
    assert (folder / "go_to_boss.tape.json").exists()
    assert "def go_to_boss():" in (folder / "go_to_boss.py").read_text(encoding="utf-8")
    caller = (folder / "count.py").read_text(encoding="utf-8")
    assert "from .go_to_boss import go_to_boss" in caller
    assert "go_to_boss()" in caller and "helper" not in caller
    assert actions_api.breakpoints(project)["go_to_boss"] == [6]
    with pytest.raises(ValueError):
        actions_api.rename(project, "go_to_boss", "count")  # taken
