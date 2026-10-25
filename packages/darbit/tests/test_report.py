"""The run report: events written while a script runs, and the summary of a day."""
import json

import numpy as np
import pytest

import darbit as d
from darbit.core.geometry import Region
from darbit.core.targets import save
from darbit.platform import screen
from darbit.tools.report import read, summary


@pytest.fixture
def logs(monkeypatch, tmp_path):
    monkeypatch.setattr(d.settings, "logs", tmp_path / "logs")
    monkeypatch.setattr(d.settings, "images", [tmp_path])
    monkeypatch.setattr(d.settings, "log", True)
    shot = np.random.default_rng(1).integers(0, 255, (200, 300, 3), dtype=np.uint8)
    monkeypatch.setattr(screen, "grab", lambda region=None: (shot.copy(), Region(0, 0, 300, 200)))
    return tmp_path / "logs"


def events(logs):
    return read(next(logs.glob("report-*.jsonl")))


def test_steps_record_how_they_ended(logs):
    with d.step("Speed Raid"), d.step("pick"):
        d.record("speed raid done", character="Naruto")
    with pytest.raises(ValueError), d.step("Boss Rush"):
        raise ValueError("no Start button")
    ends = [e for e in events(logs) if e["event"] == "step" and e["state"] != "started"]
    assert [(e["step"], e["state"]) for e in ends] == [
        ("Speed Raid > pick", "ok"), ("Speed Raid", "ok"), ("Boss Rush", "failed")]
    assert ends[2]["reason"] == "no Start button" and ends[2]["screenshot"]


def test_a_miss_records_the_closest_score(logs, tmp_path):
    save(tmp_path / "Killua", np.random.default_rng(3).integers(0, 255, (20, 30, 3), dtype=np.uint8))
    assert d.exists("Killua", 0.01) is None
    miss = [e for e in events(logs) if e["event"] == "exists"][-1]
    assert miss["found"] is None and miss["closest"] is not None and miss["closest"] < 0.7


def test_the_summary(logs, tmp_path):
    save(tmp_path / "Killua", np.random.default_rng(3).integers(0, 255, (20, 30, 3), dtype=np.uint8))
    for _ in range(2):
        with pytest.raises(RuntimeError), d.step("Speed Raid"):
            d.exists("Killua", 0.01)
            raise RuntimeError("Killua not found in the list")
    d.record("skipped", character="Killua")
    text = summary(events(logs))
    assert "Speed Raid" in text and "2x  Speed Raid: Killua not found in the list" in text
    assert "Killua" in text.split("most often not found")[1]
    assert "1x  skipped" in text


def test_a_line_cut_short_is_ignored(tmp_path):
    path = tmp_path / "report.jsonl"
    path.write_text(json.dumps({"event": "x"}) + "\n{\"event\": \"y", encoding="utf-8")
    assert read(path) == [{"event": "x"}]
