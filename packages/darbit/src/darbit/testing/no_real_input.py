"""A pytest plugin that turns real input off for a bot's tests: one line in its conftest.py,

    pytest_plugins = ["darbit.testing.no_real_input"]

sets DARBIT_NO_REAL_INPUT=1 as the tests start, for them and every process they start. A click, key, mouse move,
screen grab or app open, close or focus a test forgot to fake then raises RealInputOff naming the call, instead of
touching the PC (platform/real.py). FakeGame's fakes still work. The `real_input` fixture turns it back on for one
test that needs it.
"""

import os

import pytest

from ..platform.real import SWITCH, RealInputOff

__all__ = ["SWITCH", "RealInputOff", "real_input"]

# on at import, before the tests (and the bot they import) are collected
os.environ[SWITCH] = "1"


@pytest.fixture
def real_input(monkeypatch: pytest.MonkeyPatch) -> None:
    """Real input back on for this test only."""
    monkeypatch.delenv(SWITCH, raising=False)
