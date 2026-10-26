"""Desktop windows: the Win32 styles each kind gets (the windows themselves are checked by hand)."""

from darbit.desktop import windows


def test_bars_stay_on_top_and_never_take_focus():
    bar = windows.styles("bar")
    assert bar & windows.WS_EX_TOPMOST
    assert bar & windows.WS_EX_NOACTIVATE  # clicking it leaves the game focused
    assert bar & windows.WS_EX_TOOLWINDOW  # not in Alt+Tab
    assert not bar & windows.WS_EX_TRANSPARENT


def test_clickthrough_lets_the_mouse_through():
    assert windows.styles("clickthrough") & windows.WS_EX_TRANSPARENT
    assert windows.styles("clickthrough") & windows.WS_EX_LAYERED


def test_normal_windows_are_plain():
    assert windows.styles("normal") == 0
    assert windows.styles("overlay") == windows.WS_EX_TOPMOST
