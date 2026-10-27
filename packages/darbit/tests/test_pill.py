"""The run pill's show and hide rules, without windows or a mouse hook."""

from darbit.desktop.pill import EDGE, HIDE_AFTER, MARGIN, PEEK, Peek


def bar() -> Peek:
    """A 460 x 64 bar at the top centre of a 1920-wide screen, shown at t=0."""
    return Peek(left=730, top=0, width=460, height=64)


def test_it_hides_a_while_after_the_mouse_leaves():
    peek = bar()
    peek.mouse(900, 30, now=1.0)  # on the bar
    assert not peek.should_hide(100.0)  # stays while the mouse rests on it
    peek.mouse(900, 400, now=2.0)  # away
    assert not peek.should_hide(2.0 + HIDE_AFTER - 0.1)
    assert peek.should_hide(2.0 + HIDE_AFTER)


def test_it_hides_on_its_own_when_the_mouse_never_comes():
    assert bar().should_hide(HIDE_AFTER)


def test_only_the_top_edge_above_the_bar_brings_it_back():
    peek = bar()
    peek.shown = False
    peek.mouse(900, EDGE + 1, now=5.0)  # just below the edge
    assert not peek.shown
    peek.mouse(100, 0, now=5.0)  # the top edge, but far to the side
    assert not peek.shown
    peek.mouse(730 - MARGIN, 0, now=5.0)
    assert peek.shown
    assert not peek.should_hide(50.0)  # the mouse is on it now


def test_hidden_leaves_a_sliver_showing():
    assert bar().hidden_top() == -64 + PEEK


def test_a_bar_set_to_never_hide_stays():
    peek = bar()
    peek.hide_after = 0
    assert not peek.should_hide(1000.0)
