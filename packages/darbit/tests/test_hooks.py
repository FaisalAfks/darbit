"""Raw input: what each message means, sent input left out, and the listener starting and stopping."""

import ctypes

from darbit.platform.win32 import listener as hooks


def mouse(flags=0, data=0, dx=0, dy=0, device=1):
    raw = hooks.RAWINPUT()
    raw.header.dwType = hooks.RIM_TYPEMOUSE
    raw.header.hDevice = device
    raw.data.mouse.usButtonFlags = flags
    raw.data.mouse.usButtonData = data
    raw.data.mouse.lLastX = dx
    raw.data.mouse.lLastY = dy
    return raw


def keyboard(vk, up=False, device=1):
    raw = hooks.RAWINPUT()
    raw.header.dwType = hooks.RIM_TYPEKEYBOARD
    raw.header.hDevice = device
    raw.data.keyboard.VKey = vk
    raw.data.keyboard.Flags = hooks.RI_KEY_BREAK if up else 0
    return raw


def test_keys_go_down_and_up():
    assert hooks.events_of(keyboard(0x45), (0, 0)) == [("key_down", 0x45, 0, 0)]
    assert hooks.events_of(keyboard(0x45, up=True), (0, 0)) == [("key_up", 0x45, 0, 0)]


def test_buttons_moves_and_the_wheel_carry_the_cursor():
    assert hooks.events_of(mouse(0x0001), (10, 20)) == [("mouse_down", 0, 10, 20)]
    assert hooks.events_of(mouse(0x0008), (10, 20)) == [("mouse_up", 1, 10, 20)]
    assert hooks.events_of(mouse(dx=3), (5, 6)) == [("mouse_move", 0, 5, 6), ("mouse_delta", 1, 3, 0)]
    wheel_down = ctypes.c_ushort(-240 & 0xFFFF).value
    assert hooks.events_of(mouse(0x0400, wheel_down), (0, 0)) == [("wheel", -2, 0, 0)]


def test_sent_input_is_left_out():
    assert hooks.events_of(mouse(0x0001, device=0), (1, 1)) == []
    assert hooks.events_of(keyboard(0x45, device=0), (1, 1)) == []


def test_the_listener_starts_and_stops():
    seen = []
    stop = hooks.start(lambda *event: seen.append(event))
    assert hooks._listener.thread_id
    stop()
    assert seen == []  # nothing was pressed
