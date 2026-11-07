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
    for name in ("images", "match", "log", "space", "window"):
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
        return bench.Result("menu", target, "right", 0.99, ms, ms, 40.0, False)

    results = [result("Play", 30.0), result("Bag", 2.5), result("Shop", 11.0), result("New", 50.0)]
    baseline = {"menu/Play": 10.0, "menu/Bag": 1.0, "menu/Shop": 10.0}
    # Play: 3 times slower; Bag: 2.5 times but only 1.5 ms (noise); Shop: barely slower; New: no baseline yet
    assert bench.slower_than(results, baseline) == ["menu/Play: 30.0 ms, was 10.0 ms"]
    assert bench.slower_than(results, baseline, times=4) == []
    assert bench.baseline_of(results)["menu/Bag"] == 2.5


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
