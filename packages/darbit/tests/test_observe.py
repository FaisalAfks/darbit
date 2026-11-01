"""Observers and interrupts, with a fake screen and no background thread."""

import threading
import time

import numpy as np
import pytest

import darbit as d
from darbit.core.geometry import Region
from darbit.core.targets import save
from darbit.platform import safety, screen
from darbit.platform.win32 import input as device
from darbit.runtime import observe as obs


@pytest.fixture(autouse=True)
def clean(monkeypatch, tmp_path):
    monkeypatch.setattr(obs, "_start", lambda: None)  # ticks are run by hand
    monkeypatch.setattr(d.settings, "log", False)
    monkeypatch.setattr(d.settings, "images", [tmp_path])
    sent = []
    monkeypatch.setattr(device, "_send", lambda *e: sent.extend(e))
    monkeypatch.setattr(device, "EVENT_DELAY", 0)
    yield sent
    d.stop_observing()
    safety._pending.clear()
    safety._wake.clear()
    device._held_keys.clear()


def test_a_condition_interrupts_the_next_call_once():
    state = {"closed": False}
    d.observe(lambda: state["closed"], name="game closed")
    obs.tick()
    d.sleep(0)  # nothing yet
    state["closed"] = True
    obs.tick()
    with pytest.raises(d.Interrupted) as event:
        d.sleep(0)
    assert event.value.name == "game closed"
    obs.tick()  # still closed: no second interrupt
    d.sleep(0)


def test_it_fires_again_after_going_away_and_coming_back():
    state = {"on": True}
    observer = d.observe(lambda: state["on"], name="x")
    obs.tick()
    with pytest.raises(d.Interrupted):
        d.sleep(0)
    state["on"] = False
    obs.tick()
    state["on"] = True
    obs.tick()
    with pytest.raises(d.Interrupted):
        d.sleep(0)
    assert observer.fired == 2


def test_an_image_observer_shares_one_capture(monkeypatch, tmp_path):
    rng = np.random.default_rng(1)
    shown = rng.integers(0, 255, (300, 400, 3), dtype=np.uint8)
    sign = np.random.default_rng(2).integers(0, 255, (20, 30, 3), dtype=np.uint8)
    save(tmp_path / "Disconnected", sign)
    save(tmp_path / "Other", np.random.default_rng(3).integers(0, 255, (20, 30, 3), dtype=np.uint8))
    grabs = []

    def grab(region=None):
        grabs.append(region)
        return shown.copy(), Region(0, 0, 400, 300)

    monkeypatch.setattr(screen, "grab", grab)
    d.observe("Disconnected")
    d.observe("Other")
    obs.tick()
    assert len(grabs) == 1
    d.sleep(0)
    shown[100:120, 50:80] = sign
    obs.tick()
    with pytest.raises(d.Interrupted) as event:
        d.sleep(0)
    assert event.value.name == "Disconnected" and (event.value.match.x, event.value.match.y) == (50, 100)


def test_no_interrupts_inside_a_quiet_block():
    d.observe(lambda: True, name="x")
    with d.no_interrupts():
        obs.tick()
        d.sleep(0)


def test_an_interrupt_lets_go_of_held_keys(clean):
    d.hold("w")
    d.observe(lambda: True, name="x")
    obs.tick()
    with pytest.raises(d.Interrupted):
        d.press("a")
    assert not device._held_keys
    assert clean[-1].ki.dwFlags & 0x0002  # the last event was a key up


def test_a_sleep_wakes_up_for_an_interrupt():
    d.observe(lambda: True, name="x")
    threading.Timer(0.1, obs.tick).start()
    started = time.monotonic()
    with pytest.raises(d.Interrupted):
        d.sleep(5)
    assert time.monotonic() - started < 1


def test_image_observers_grab_only_the_area_they_watch(monkeypatch, tmp_path):
    sign = np.random.default_rng(2).integers(0, 255, (20, 30, 3), dtype=np.uint8)
    save(tmp_path / "Left", sign, region=[10, 20, 100, 50])
    save(tmp_path / "Right", sign, region=[200, 40, 50, 100])
    save(tmp_path / "Anywhere", sign)
    grabs = []

    def grab(region=None):
        grabs.append(region)
        return np.zeros((300, 400, 3), np.uint8), region or Region(0, 0, 400, 300)

    monkeypatch.setattr(screen, "grab", grab)
    left = d.observe("Left")
    d.observe("Right")
    obs.tick()
    assert grabs[-1] == Region(10, 20, 240, 120)  # both areas, and nothing else
    d.observe("Anywhere")
    obs.tick()
    assert grabs[-1] is None  # one without an area of its own needs the whole screen
    left.stop()
    obs.tick()
    assert grabs[-1] is None
