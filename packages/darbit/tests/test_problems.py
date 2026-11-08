"""Why a step failed: the searches that ran out before it, a likely cause, and failures grouped by it."""

import json
from datetime import datetime

import pytest

from darbit.project.manifest import load
from darbit.server import problems


@pytest.fixture
def project(tmp_path):
    (tmp_path / "darbit.toml").write_text('[bot]\nname = "fish-bot"\n[settings]\nsimilarity = 0.85\n', encoding="utf-8")
    (tmp_path / "images").mkdir()
    (tmp_path / "images" / "Rod.Cast.json").write_text(
        json.dumps({"kind": "image", "similarity": 0.6}), encoding="utf-8"
    )
    return load(tmp_path)


def at(clock):
    return f"2026-11-01T{clock}.000"


def search(clock, name, timeout, closest=None, found=None):
    event = {"time": at(clock), "event": "exists", "targets": name + ".png", "timeout": timeout}
    if found:
        return {**event, "found": name + ".png", "score": 0.99}
    return {
        **event,
        "found": None,
        "closest": closest,
        "closest_name": name + ".png",
        "at": [10, 20],
        "screenshot": None,
    }


def run(start, end, *middle, reason="the rod couldn't be cast"):
    return [
        {"time": at(start), "event": "step", "step": "Fishing", "state": "started"},
        *middle,
        {
            "time": at(end),
            "event": "step",
            "step": "Fishing",
            "state": "failed",
            "reason": reason,
            "screenshot": "x.jpg",
        },
    ]


def test_an_image_seen_today_then_far_off_was_likely_covered(project, tmp_path):
    events = [
        search("09:00:00", "Gui.Rod", 60, found=True),
        *run("10:00:00", "10:02:30", search("10:01:00", "Gui.Rod", 60, 0.46), search("10:02:00", "Gui.Rod", 60, 0.46)),
        *run("12:00:00", "12:02:30", search("12:01:00", "Gui.Rod", 120, 0.44)),
    ]
    found = problems.explain(project, events, tmp_path)
    assert len(found) == 1 and found[0]["count"] == 2  # the same cause, step, reason and image: one problem
    assert found[0]["cause"] == problems.COVERED and not found[0]["act"]
    assert found[0]["searches"][0] == {
        "target": "Gui.Rod",
        "seconds": 120,
        "closest": 0.44,
        "needs": 0.85,
        "at": [10, 20],
        "picture": None,
        "screenshot": None,
    }
    assert "Gui.Rod for 2 minutes" in found[0]["sentence"]


def test_close_but_under_the_line_looks_different_and_far_never_seen_is_missing(project, tmp_path):
    changed = problems.explain(project, run("10:00:00", "10:01:00", search("10:00:50", "Rod.Cast", 45, 0.52)), tmp_path)
    assert changed[0]["cause"] == problems.CHANGED and changed[0]["act"]  # 0.52 of the 0.60 Rod.Cast needs
    missing = problems.explain(project, run("10:00:00", "10:01:00", search("10:00:50", "Gui.Net", 45, 0.2)), tmp_path)
    assert missing[0]["cause"] == problems.MISSING


def test_a_short_check_or_a_watched_image_is_the_bots_own_reason(project, tmp_path):
    events = [
        {"time": at("09:00:00"), "event": "observer", "name": "Disconnected.png", "state": "watching"},
        *run(
            "10:00:00",
            "10:05:00",
            search("10:01:00", "Disconnected", 300, 0.4),  # watched for: meant not to be there
            search("10:02:00", "Fish.Any", 0, 0.1),  # a look with no wait
            search("10:04:50", "Fish.Claim", 15, 0.27),
            reason="no fish to collect",
        ),
    ]
    found = problems.explain(project, events, tmp_path)
    assert found[0]["cause"] == problems.OWN
    assert [row["target"] for row in found[0]["searches"]] == ["Fish.Claim"]
    assert "Fish.Claim wasn't there after 15 s" in found[0]["sentence"]


def test_a_problem_has_the_last_steps_before_its_failure(project, tmp_path):
    middle = [
        {"time": at("10:00:01"), "event": "step", "step": "Fishing > Cast", "state": "started"},
        {"time": at("10:00:02"), "event": "click", "target": "Rod.Cast.png", "done": True, "at": [5, 5]},
        {"time": at("10:00:03"), "event": "gain", "name": "Gold", "amount": 1},  # not a step: left out
        {"time": at("10:00:04"), "event": "step", "step": "Fishing > Cast", "state": "ok", "seconds": 3},
        {"time": at("10:00:05"), "event": "go", "to": "Lake", "state": "there"},
        {"time": at("10:00:06"), "event": "wait", "targets": "Gui.Bite.png", "timeout": 5, "found": "Gui.Bite.png"},
        {"time": at("10:00:07"), "event": "click", "target": "Gui.Reel", "done": False},
        search("10:00:50", "Rod.Cast", 45, 0.52),
    ]
    found = problems.explain(project, run("10:00:00", "10:01:00", *middle), tmp_path)
    steps = found[0]["before"]
    assert [step["say"] for step in steps] == [
        "Cast: started",
        "click Rod.Cast",
        "Cast: ok",
        "go to Lake: there",
        "wait Gui.Bite: found",
        "click Gui.Reel: not found",
        "exists Rod.Cast: not found in 45 s (closest 0.52)",
    ]
    assert [step["ok"] for step in steps] == [True, True, True, True, True, False, False]
    assert steps[-1]["time"] == at("10:00:50") and steps[-1]["kind"] == "exists"
    many = [search(f"10:00:{second:02}", "Fish.Any", 0, 0.1) for second in range(10, 30)]
    found = problems.explain(project, run("10:00:00", "10:01:00", *many), tmp_path)
    assert len(found[0]["before"]) == problems.BEFORE  # the last few only
    assert found[0]["before"][-1]["time"] == at("10:00:29")


def test_the_overview_gets_the_explained_problems(project, tmp_path):
    from darbit.server import overview

    events = run("10:00:00", "10:01:00", search("10:00:50", "Rod.Cast", 45, 0.52))
    found = overview.data(project, events, "2026-11-01", datetime(2026, 11, 1, 11), tmp_path)
    assert found["problems"][0]["cause"] == problems.CHANGED and found["problems"][0]["tone"] == "danger"


# ---- an image that may have stopped matching


def test_two_failures_in_a_row_on_one_image_say_it_may_have_stopped_matching(project):
    events = [
        *run("10:00:00", "10:02:30", search("10:01:00", "Team.Card", 60, 0.32)),
        *run("10:30:00", "10:32:30", search("10:31:00", "Team.Card", 60, 0.6)),
    ]
    found = problems.failing(project, events[: len(events) // 2])
    assert found is None  # one failure is just a failure
    found = problems.failing(project, events)
    assert found["target"] == "Team.Card" and found["count"] == 2
    assert found["since"] == at("10:02:30") and found["closest"] == 0.6 and found["needs"] == 0.85
    assert "failed 2 times in a row" in found["sentence"] and "retake it" in found["sentence"]
    assert not found["seen_before"]


def test_found_again_or_another_reason_ends_it(project):
    two = [
        *run("10:00:00", "10:02:30", search("10:01:00", "Team.Card", 60, 0.32)),
        *run("10:30:00", "10:32:30", search("10:31:00", "Team.Card", 60, 0.32)),
    ]
    assert problems.failing(project, [*two, search("11:00:00", "Team.Card", 60, found=True)]) is None
    assert problems.failing(project, [*two, *run("11:00:00", "11:00:05", reason="the bot's own")]) is None
    other = run("11:00:00", "11:02:30", search("11:01:00", "Gui.Rod", 60, 0.1))
    assert problems.failing(project, [*two, *other]) is None  # a different image: one failure of it so far


def test_an_image_found_earlier_today_may_be_covered(project):
    events = [
        search("09:00:00", "Team.Card", 60, found=True),
        *run("10:00:00", "10:02:30", search("10:01:00", "Team.Card", 60, 0.32)),
        *run("10:30:00", "10:32:30", search("10:31:00", "Team.Card", 60, 0.32)),
    ]
    found = problems.failing(project, events)
    assert found["seen_before"] and "a window over the game" in found["sentence"]


def test_reads_are_among_the_last_steps_before_a_failure():
    from darbit.server import problems

    run = [
        {"event": "step", "step": "Shop", "state": "started"},
        {"event": "read_number", "target": "Shop.Coins", "text": "4.99M", "confidence": 0.98, "counted": True},
        {"event": "read_time", "target": "Run.Timer", "text": "0z", "confidence": 0.2, "counted": False},
        {"event": "log", "line": "not a step"},  # control: what isn't a step stays out
    ]
    rows = problems.before(run)
    assert [row["say"] for row in rows] == ["read number Shop.Coins: '4.99M'", "read time Run.Timer: unreadable"]
    assert [row["ok"] for row in rows] == [True, False]
