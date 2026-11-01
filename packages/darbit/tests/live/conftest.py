"""The live tests: darbit on a real Windows desktop, on a window of its own (target.py). They move the mouse and
press keys for real, so they run only where DARBIT_LIVE=1 is set: the CI's fresh Windows machine, never by accident
on a PC someone is using."""

import json
import os
import subprocess
import sys
import time
from pathlib import Path

import cv2
import numpy as np
import pytest

HERE = Path(__file__).parent
PICTURE = "live_patch"  # the picture target.py shows (the same name is in target.py)


class Target:
    """The target window running in its own process, and what it wrote down."""

    def __init__(self, folder: Path) -> None:
        self.events_file = folder / "events.jsonl"
        self.events_file.write_text("", encoding="utf-8")
        environment = dict(os.environ, QT_ENABLE_HIGHDPI_SCALING="0")
        self.process = subprocess.Popen(
            [sys.executable, str(HERE / "target.py"), str(folder / f"{PICTURE}.png"), str(self.events_file)],
            env=environment,
        )
        self.client = self._ready()

    def _ready(self) -> dict:
        deadline = time.monotonic() + 20
        while time.monotonic() < deadline:
            for event in self.events():
                if event["kind"] == "ready":
                    return event
            time.sleep(0.1)
        raise RuntimeError("the target window didn't show")

    def events(self, kind: str | None = None) -> list[dict]:
        lines = self.events_file.read_text(encoding="utf-8").splitlines()
        found = [json.loads(line) for line in lines if line.strip()]
        if kind is None:
            return found
        return [event for event in found if event["kind"] == kind]

    def settle(self, seconds: float = 0.3) -> None:
        """Give the window time to take what was sent."""
        time.sleep(seconds)

    def close(self) -> None:
        self.process.terminate()
        self.process.wait(10)


@pytest.fixture(scope="session")
def pictures(tmp_path_factory) -> Path:
    """A folder with one picture: noise, so it can only be found where it is."""
    folder = tmp_path_factory.mktemp("pictures")
    noise = np.random.default_rng(7).integers(0, 256, (48, 64, 3), dtype=np.uint8)
    cv2.imwrite(str(folder / f"{PICTURE}.png"), noise)
    return folder


@pytest.fixture(scope="session")
def target(pictures):
    window = Target(pictures)
    yield window
    window.close()


@pytest.fixture(autouse=True)
def darbit_settings(pictures, monkeypatch):
    import darbit as d

    monkeypatch.setattr(d.settings, "images", [pictures])
    monkeypatch.setattr(d.settings, "glide", 0.1)
    monkeypatch.setattr(d.settings, "timeout", 3.0)
    return d.settings


def pytest_collection_modifyitems(config, items):
    if sys.platform != "win32" or os.environ.get("DARBIT_LIVE") != "1":
        skip = pytest.mark.skip(reason="live tests run only on Windows with DARBIT_LIVE=1")
        for item in items:
            if HERE in Path(item.fspath).parents:  # this hook sees every test: skip only the live ones
                item.add_marker(skip)
