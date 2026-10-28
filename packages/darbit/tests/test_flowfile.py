"""Actions as Python: read into sections and steps with their lines, and written back unchanged."""

import pytest

from darbit.runs import flowfile
from darbit.runs.flowfile import Section, Step

ACTION = '''"""Fight one wave."""

import darbit as d
from .dodge import dodge


@d.flow
def fight():
    d.press("q")  # opener
    with d.step("Wave 1"):
        d.hold("w")
        d.sleep(0.5)
        d.release("w")
        d.click("Fight.Skill2")
        d.click(d.Location(812, 440))
        d.wait("Dim.Game.Left", timeout=30)
        if d.exists("Dim.Boss.Bar", 0.5):
            dodge()
        while not d.exists("Dim.Game.Leave"):
            d.press("shift", "e")
        for _ in range(3):
            d.write("gg")
        total = 2 + 2
    with d.step("Leave"):
        d.vanish("Dim.Loading", timeout=10)
'''


def test_an_action_reads_into_sections_and_steps(tmp_path):
    path = tmp_path / "fight.py"
    path.write_text(ACTION, encoding="utf-8")
    flow = flowfile.read(path)
    assert flow.name == "fight"
    assert flow.docstring == "Fight one wave."
    assert flow.calls == ["dodge"]
    assert [section.name for section in flow.sections] == ["", "Wave 1", "Leave"]
    opener = flow.sections[0].steps[0]
    assert (opener.kind, opener.args, opener.note, opener.line) == (
        "key",
        {"verb": "press", "keys": ["q"]},
        "opener",
        9,
    )
    wave = flow.sections[1].steps
    kinds = [step.kind for step in wave]
    assert kinds == ["key", "wait", "key", "mouse", "mouse", "check", "if", "loop", "loop", "code"]
    assert wave[4].args == {"verb": "click", "target": [812, 440]}
    assert wave[5].args == {"verb": "wait for", "target": "Dim.Game.Left", "timeout": 30}
    assert wave[6].children[0].args == {"name": "dodge", "action": True}
    assert wave[7].args == {"until": "Dim.Game.Leave"}
    assert wave[8].args == {"times": 3}
    assert wave[9].source == "total = 2 + 2"


def test_writing_gives_the_same_file_back(tmp_path):
    path = tmp_path / "fight.py"
    path.write_text(ACTION, encoding="utf-8")
    flow = flowfile.read(path)
    assert flowfile.render(flow.name, flow.sections, flow.docstring, flow.calls) == ACTION


def test_new_steps_become_python():
    sections = [
        Section("Wave 1", [Step("key", {"verb": "press", "keys": ["e"]}, "skill"), Step("wait", {"seconds": 0.25})])
    ]
    text = flowfile.render("dodge", sections)
    assert '    with d.step("Wave 1"):\n        d.press("e")  # skill\n        d.sleep(0.25)\n' in text
    assert "@d.flow\ndef dodge():" in text
    compile(text, "dodge.py", "exec")


def test_steps_go_to_the_studio_and_back():
    step = Step("if", {"verb": "if seen", "target": "X", "timeout": 1}, "", 3, "", [Step("call", {"name": "dodge"})])
    assert flowfile.from_dict(flowfile.to_dict(step)) == step


def test_a_file_without_an_action_says_so(tmp_path):
    path = tmp_path / "helpers.py"
    path.write_text("x = 1\n", encoding="utf-8")
    with pytest.raises(flowfile.FlowError, match="no @d.flow"):
        flowfile.read(path)
    path.write_text("def (:\n", encoding="utf-8")
    with pytest.raises(flowfile.FlowError, match="line 1"):
        flowfile.read(path)


def test_d_flow_marks_the_function():
    import darbit as d

    @d.flow
    def run():
        return 1

    assert run.darbit_flow is True
    assert run() == 1


def test_a_recorded_action_stays_timed_and_keeps_its_camera_turns(tmp_path):
    steps = [
        Step("mouse", {"verb": "mouse_down", "target": [960, 540], "button": "right"}),
        Step("mouse", {"verb": "move_by", "by": [-120, 8], "seconds": 0.2}),
        Step("mouse", {"verb": "mouse_up", "target": None, "button": "right"}),
        Step("wait", {"seconds": 0.37}),
        Step("key", {"verb": "press", "keys": ["shift+e"]}),
    ]
    text = flowfile.render("run", [Section("Run", steps)], timed=True)
    assert "@d.flow(timed=True)" in text
    assert "d.move_by(-120, 8, 0.2)" in text
    assert 'd.mouse_down(d.Location(960, 540), button="right")' in text
    assert 'd.mouse_up(button="right")' in text
    path = tmp_path / "run.py"
    path.write_text(text, encoding="utf-8")
    flow = flowfile.read(path)
    assert flow.timed
    found = []
    for step in flow.sections[0].steps:
        found.append((step.kind, step.args))
    assert found[1] == ("mouse", {"verb": "move_by", "by": [-120, 8], "seconds": 0.2})
    assert found[2] == ("mouse", {"verb": "mouse_up", "target": None, "button": "right"})
    assert flowfile.render("run", flow.sections, timed=flow.timed) == text


def test_a_timed_action_keeps_to_its_schedule(monkeypatch):
    import time

    import darbit as d
    from darbit.platform import safety
    from darbit.runtime import actions

    slept = []

    def sleep(seconds):
        slept.append(seconds)
        time.sleep(seconds)

    monkeypatch.setattr(safety, "sleep", sleep)

    @d.flow(timed=True)
    def run():
        actions.sleep(0.2)
        time.sleep(0.05)  # a step that took 0.05 s
        actions.sleep(0.2)

    run()
    assert slept[0] == pytest.approx(0.2, abs=0.02)
    assert slept[1] == pytest.approx(0.15, abs=0.02)  # the step's 0.05 s came out of this wait
    assert run.darbit_flow is True
    actions.sleep(0)  # outside a timed action, a sleep is just a sleep
    assert slept[2] == 0
