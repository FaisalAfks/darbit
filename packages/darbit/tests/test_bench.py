"""`darbit bench`: judging answers, the speed gate against a baseline, cases from saved screens, and a whole run."""

import json
from pathlib import Path
from types import SimpleNamespace

import cv2
import numpy as np
import pytest

import darbit as d
from darbit.platform import screen
from darbit.runtime import find
from darbit.tools import bench


@pytest.fixture
def isolated(monkeypatch):
    """A bench run swaps darbit's screen, windows and settings: put them all back after the test."""
    monkeypatch.setattr(screen, "grab", screen.grab)
    monkeypatch.setattr(screen, "scale_at", screen.scale_at)
    monkeypatch.setattr(find.windows, "matching", find.windows.matching)
    monkeypatch.setattr(find.windows, "region", find.windows.region)
    for name in ("images", "match", "read", "log", "space", "window"):
        monkeypatch.setattr(d.settings, name, getattr(d.settings, name))


def make_case(folder, absent=False):
    """A 400 x 300 noisy screen with a 40 x 30 patch to find, and the patch as the target."""
    rng = np.random.default_rng(3)
    pixels = rng.integers(0, 255, (300, 400, 3), dtype=np.uint8)
    (folder / "images").mkdir(parents=True)
    cv2.imwrite(str(folder / "screen.png"), pixels)
    cv2.imwrite(str(folder / "images" / "Patch.png"), pixels[100:130, 200:240])
    find_line = "absent = true" if absent else "at = [200, 100, 40, 30]"
    (folder / "case.toml").write_text(f'[[find]]\ntarget = "Patch"\n{find_line}\n', encoding="utf-8")


def test_answers_are_judged_by_how_much_the_boxes_overlap():
    match = SimpleNamespace(x=10, y=10, w=20, h=20)
    assert bench.judge(match, {"at": [10, 10, 20, 20]}) == "right"
    assert bench.judge(match, {"at": [100, 100, 20, 20]}) == "wrong place"
    assert bench.judge(match, {}) == "false match"
    assert bench.judge(None, {"at": [0, 0, 5, 5]}) == "missed"
    assert bench.judge(None, {}) == "right"
    assert bench.overlap([0, 0, 10, 10], [5, 0, 10, 10]) == pytest.approx(1 / 3)


def test_a_search_much_slower_than_its_baseline_fails_but_noise_does_not():
    def result(target, ms):
        return bench.Result("menu", target, "right", 0.99, ms, ms, ms, 40.0, False)

    results = [result("Play", 30.0), result("Bag", 2.5), result("Shop", 11.0), result("New", 50.0)]
    baseline = {"menu/Play": 10.0, "menu/Bag": 1.0, "menu/Shop": 10.0}
    # Play: 3 times slower; Bag: 2.5 times but only 1.5 ms (noise); Shop: barely slower; New: no baseline yet
    assert bench.slower_than(results, baseline) == ["menu/Play: 30.0 ms, was 10.0 ms"]
    assert bench.slower_than(results, baseline, times=4) == []
    assert bench.baseline_of(results)["menu/Bag"] == 2.5


def timed(target, fastest, median=None):
    """A right search of the menu case: its fastest repeat, and its median (the fastest if not given)."""
    median = fastest if median is None else median
    return bench.Result("menu", target, "right", 0.99, fastest, median, median, 40.0, False)


MENU = {"menu/Play": 20.0, "menu/Shop": 18.0, "menu/Bag": 16.0, "menu/Claim": 30.0, "menu/Close": 1.5}


def test_the_gate_compares_the_fastest_repeat_not_the_median():
    noisy = [timed("Play", 21.0, median=45.0)]  # one slow spell among the repeats: the fastest is as before
    assert bench.slower_than(noisy, MENU) == []
    slow = [timed("Play", 45.0)]  # control: every repeat slower
    assert bench.slower_than(slow, MENU) == ["menu/Play: 45.0 ms, was 20.0 ms"]
    assert bench.baseline_of(noisy) == {"menu/Play": 21.0}


def test_a_slow_machine_moves_every_search_alike_and_passes():
    # a shared runner about 2.2 times slower for the whole job; Close is too short to say
    run = [timed(name.split("/")[1], ms * 2.2) for name, ms in MENU.items()]
    assert bench.machine_speed(run, MENU) == pytest.approx(2.2)
    assert bench.slower_than(run, MENU) == []
    # control: judged without allowing for the machine, the run and every long search would fail
    assert len(bench.slower_than(run, MENU, machine=1.0)) == 1 + 4


def test_one_search_much_slower_than_the_rest_fails_on_a_slow_machine_too():
    run = [timed("Play", 20.0 * 2 * 2.5), timed("Shop", 36.0), timed("Bag", 32.0), timed("Claim", 60.0)]
    assert bench.machine_speed(run, MENU) == pytest.approx(2.0)
    assert bench.slower_than(run, MENU) == ["menu/Play: 100.0 ms, was 20.0 ms (the run as a whole 2.0 times slower)"]
    # control: the same search only as slow as the rest passes
    run[0] = timed("Play", 40.0)
    assert bench.slower_than(run, MENU) == []


def test_one_search_twice_as_slow_on_a_normal_machine_fails():
    run = [timed("Play", 45.0), timed("Shop", 18.5), timed("Bag", 15.8), timed("Claim", 31.0)]
    assert bench.machine_speed(run, MENU) < 1.1
    assert bench.slower_than(run, MENU) == ["menu/Play: 45.0 ms, was 20.0 ms"]


def test_a_whole_run_far_slower_than_any_machine_fails():
    run = [timed(name.split("/")[1], ms * 4) for name, ms in MENU.items()]
    slow = bench.slower_than(run, MENU)
    assert slow == ["the whole run: 4.0 times slower than the baseline (a slow machine may be 3)"]
    assert bench.slower_than(run, MENU, machine=5.0) == []  # control: allowed with a larger --machine-slower


def test_a_faster_machine_does_not_make_the_gate_stricter():
    run = [timed("Play", 30.0), timed("Shop", 9.0), timed("Bag", 8.0), timed("Claim", 15.0)]
    assert bench.machine_speed(run, MENU) == pytest.approx(0.5)
    assert bench.slower_than(run, MENU) == []  # Play is 3 times the others, but within 2 times its baseline


def test_too_few_searches_leave_the_machine_alone():
    run = [timed("Play", 50.0), timed("Shop", 45.0)]
    assert bench.machine_speed(run, MENU) == 1.0
    assert len(bench.slower_than(run, MENU)) == 2


def test_a_whole_run_finds_the_patch_and_writes_a_baseline(tmp_path, isolated, capsys):
    make_case(tmp_path / "cases" / "noise")
    saved = tmp_path / "baseline.json"
    code = bench.main([str(tmp_path / "cases"), "--repeat", "2", "--save-baseline", str(saved)])
    assert code == 0
    assert "1 of 1 right" in capsys.readouterr().out
    assert set(json.loads(saved.read_text(encoding="utf-8"))) == {"noise/Patch"}


def test_a_wrong_answer_or_a_slowdown_fails_the_run(tmp_path, isolated, capsys):
    make_case(tmp_path / "cases" / "noise", absent=True)  # the patch is there, but the case says it isn't
    assert bench.main([str(tmp_path / "cases"), "--repeat", "1"]) == 1
    make_case(tmp_path / "fine" / "noise")
    baseline = tmp_path / "baseline.json"
    baseline.write_text(json.dumps({"noise/Patch": 0.0001}), encoding="utf-8")
    assert bench.main([str(tmp_path / "fine"), "--repeat", "1", "--baseline", str(baseline), "--slower", "1"]) == 1
    assert "1 more than 1 times slower" in capsys.readouterr().out


def test_cases_come_from_the_screens_the_studio_saved(tmp_path, monkeypatch):
    bot = tmp_path / "bot"
    (bot / ".darbit" / "screens").mkdir(parents=True)
    (bot / "images").mkdir()
    (bot / "darbit.toml").write_text('[images]\nfolders = ["images"]\n', encoding="utf-8")
    cv2.imwrite(str(bot / ".darbit" / "screens" / "Lobby.jpg"), np.zeros((50, 50, 3), np.uint8))
    cv2.imwrite(str(bot / "images" / "Lobby.Play.png"), np.zeros((5, 5, 3), np.uint8))
    (bot / "images" / "Lobby.Play.json").write_text('{"scale": 1.5, "region": "Lobby.Buttons"}', encoding="utf-8")
    (bot / "images" / "Lobby.Buttons.json").write_text('{"kind": "region", "region": [0, 0, 40, 40]}', encoding="utf-8")
    places = {"assets": {"Lobby.Play": {"kind": "image", "box": [1, 2, 5, 5]}, "Lobby.Spot": {"kind": "location"}}}
    (bot / ".darbit" / "screens" / "Lobby.json").write_text(json.dumps(places), encoding="utf-8")

    assert bench.from_screens(bot, tmp_path / "cases") == 1
    case = (tmp_path / "cases" / "Lobby" / "case.toml").read_text(encoding="utf-8")
    assert "scale = 1.5" in case
    assert 'target = "Lobby.Play"' in case and "at = [1, 2, 5, 5]" in case
    assert "Lobby.Spot" not in case
    assert (tmp_path / "cases" / "Lobby" / "images" / "Lobby.Play.png").is_file()
    assert (tmp_path / "cases" / "Lobby" / "images" / "Lobby.Buttons.json").is_file()  # its shared region comes too

    monkeypatch.chdir(bot)  # run from inside the bot's folder: `--from-screens .`
    assert bench.from_screens(Path("."), tmp_path / "here") == 1
    here = (tmp_path / "here" / "Lobby" / "case.toml").read_text(encoding="utf-8")
    assert here.startswith("# bot's Lobby screen")


def test_reads_are_judged_against_the_text_number_or_time_expected():
    assert bench.judge_read("Daily quest", {"text": "Daily quest"}) == "right"
    assert bench.judge_read("Daily guest", {"text": "Daily quest"}) == "misread 'Daily guest'"
    assert bench.judge_read(4990000.0, {"number": 4990000}) == "right"
    assert bench.judge_read(499.0, {"number": 4990000}) == "misread 499"
    assert bench.judge_read(151.0, {"time": 151}) == "right"
    assert bench.judge_read(None, {"time": 151}) == "missed"


class SaysNumber:
    def line(self, pixels, allowed):
        from darbit.core.reading import Reading

        return Reading("4.99M", 0.98)

    def lines(self, pixels, allowed):
        return []


def test_a_run_reads_text_and_says_when_it_needs_the_ocr_extra(tmp_path, isolated, monkeypatch, capsys):
    from darbit.runtime import readers

    make_case(tmp_path / "cases" / "noise")
    case = tmp_path / "cases" / "noise" / "case.toml"
    case.write_text(case.read_text(encoding="utf-8") + "\n[[read]]\nregion = [0, 0, 80, 30]\nnumber = 4990000\n")
    monkeypatch.setattr(readers, "current", lambda: SaysNumber())
    assert bench.main([str(tmp_path / "cases"), "--repeat", "2"]) == 0
    out = capsys.readouterr().out
    assert "2 of 2 right" in out and "read 0,0,80,30" in out and "0.980" in out
    monkeypatch.setattr(readers, "current", lambda: None)  # control: no reader, the read isn't counted
    assert bench.main([str(tmp_path / "cases"), "--repeat", "1"]) == 0
    out = capsys.readouterr().out
    assert "needs ocr" in out and "1 of 1 right" in out and "need the ocr extra" in out


def test_the_speed_gate_covers_reads_and_fails_when_they_did_not_run():
    def result(target, ms, answer="right"):
        return bench.Result("menu", target, answer, 0.99, ms, ms, ms, bench.GOAL_READ, True)

    baseline = {"menu/Top.Coins": 16.0, "menu/Top.Timer": 16.0}
    slow_read = [result("Top.Coins", 50.0), result("Top.Timer", 17.0)]
    assert bench.slower_than(slow_read, baseline) == ["menu/Top.Coins: 50.0 ms, was 16.0 ms"]
    skipped = [result("Top.Coins", 0.0, "needs ocr"), result("Top.Timer", 17.0)]
    assert bench.not_run(skipped, baseline) == ["menu/Top.Coins: not run (it needs the ocr extra), was 16.0 ms"]
    assert bench.not_run(skipped, {}) == []  # control: a read with no time in the baseline isn't missed
