"""Mouse and keyboard, recorded instead of sent: nothing moves or types."""

import pytest

import darbit as d
from darbit.platform.keys import key
from darbit.platform.win32 import input as device

KEYUP, UNICODE = 0x0002, 0x0004


@pytest.fixture
def sent(monkeypatch):
    events = []
    monkeypatch.setattr(device, "_send", lambda *e: events.extend(e))
    monkeypatch.setattr(device, "EVENT_DELAY", 0)
    monkeypatch.setattr(device, "DRAG_DELAY", 0)
    monkeypatch.setattr(d.settings, "glide", 0)
    monkeypatch.setattr(d.settings, "log", False)
    yield events
    device._held_keys.clear()
    device._held_buttons.clear()


def keys(events):
    """(key name or character, up?) for each keyboard event."""
    names = {k.scan: k.name for k in (key(n) for n in "abcdefghijklmnopqrstuvwxyz0123456789")}
    names.update({key(n).scan: n for n in ("tab", "shift", "ctrl", "alt", "enter", "esc")})
    out = []
    for e in events:
        if e.type != 1:
            continue
        up = bool(e.ki.dwFlags & KEYUP)
        out.append((chr(e.ki.wScan) if e.ki.dwFlags & UNICODE else names[e.ki.wScan], up))
    return out


def test_press_each_key_in_order(sent):
    d.press(*"541")
    assert keys(sent) == [("5", False), ("5", True), ("4", False), ("4", True), ("1", False), ("1", True)]


def test_press_combo_holds_the_first_keys(sent):
    d.press("ctrl+a")
    assert keys(sent) == [("ctrl", False), ("a", False), ("a", True), ("ctrl", True)]


def test_hold_then_release_everything(sent):
    d.hold("w", "shift")
    d.release()
    assert keys(sent) == [("w", False), ("shift", False), ("shift", True), ("w", True)]
    assert not device._held_keys


def test_holding_twice_sends_one_press(sent):
    d.hold("w")
    d.hold("w")
    d.release("w")
    assert keys(sent) == [("w", False), ("w", True)]


def test_write_sends_characters(sent):
    d.write("hé")
    assert keys(sent) == [("h", False), ("h", True), ("é", False), ("é", True)]


def test_click_at_a_location_moves_then_presses(sent):
    assert d.click(d.Location(10, 20))
    mouse = [e for e in sent if e.type == 0]
    assert mouse[-2].mi.dwFlags == 0x0002 and mouse[-1].mi.dwFlags == 0x0004  # left down, left up
    assert all(e.mi.dwFlags & 0x0001 for e in mouse[:-2])  # moves before


def test_stop_lets_go_and_stops_calls(sent, monkeypatch):
    from darbit.platform import safety

    d.hold("w")
    safety.stop()
    try:
        assert keys(sent)[-1] == ("w", True)
        with pytest.raises(d.Stopped):
            d.press("a")
        with pytest.raises(d.Stopped):
            d.sleep(5)
    finally:
        safety._stopped.clear()
