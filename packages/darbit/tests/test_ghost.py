"""The ghost cursor: bots tell their clicks and keys over a local UDP port, and the Studio keeps them for a moment."""

import json
import socket
import time

import pytest

from darbit import paths
from darbit.platform import ghost as told

QtCore = pytest.importorskip("PySide6.QtCore")


@pytest.fixture
def data(tmp_path, monkeypatch):
    monkeypatch.setattr(paths, "data_dir", lambda: tmp_path)
    told.forget()
    yield tmp_path
    told.forget()


def test_nothing_is_sent_without_a_studio(data):
    assert not told.listening()
    told.tell("click", x=1, y=2, button="left")  # no file: lost, no error


def test_a_click_reaches_the_port_in_the_ghost_file(data):
    listener = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    listener.bind(("127.0.0.1", 0))
    listener.settimeout(2)
    (data / "ghost.json").write_text(json.dumps({"port": listener.getsockname()[1]}), encoding="utf-8")
    told.forget()
    told.tell("click", x=10, y=20, button="left")
    message = json.loads(listener.recv(1024))
    listener.close()
    assert message == {"kind": "click", "x": 10, "y": 20, "button": "left"}


def test_a_broken_ghost_file_is_no_studio(data):
    (data / "ghost.json").write_text("{nope", encoding="utf-8")
    told.forget()
    assert not told.listening()


def test_the_studio_listens_keeps_marks_and_lets_them_go(data, monkeypatch):
    from PySide6.QtGui import QGuiApplication

    from darbit.studio import ghost as studio_ghost

    app = QGuiApplication.instance() or QGuiApplication(["test"])  # the Studio's tests need a GUI one
    monkeypatch.setattr(studio_ghost, "SHOWN", 0.3)
    ghost = studio_ghost.Ghost()
    ghost.start()
    assert ghost.isOn and (data / "ghost.json").is_file()
    told.forget()
    told.tell("click", x=5, y=6, button="right")
    told.tell("key", x=5, y=6, name="e")
    deadline = time.monotonic() + 3
    while len(ghost.marks) < 2 and time.monotonic() < deadline:
        app.processEvents()
        time.sleep(0.01)
    assert [(mark["kind"], mark["name"]) for mark in ghost.marks] == [("click", "right"), ("key", "e")]
    deadline = time.monotonic() + 3
    while ghost.marks and time.monotonic() < deadline:
        app.processEvents()
        time.sleep(0.02)
    assert ghost.marks == []
    ghost.stop()
    assert not ghost.isOn and not (data / "ghost.json").exists()


def test_odd_messages_are_left_out(data):
    from darbit.studio.ghost import MOST, Ghost

    ghost = Ghost()
    ghost.take({"kind": "shout"})
    ghost.take({"kind": "click", "x": "here"})
    assert ghost.marks == []
    for number in range(MOST + 5):
        ghost.take({"kind": "key", "name": str(number)})
    assert len(ghost.marks) == MOST and ghost.marks[-1]["name"] == str(MOST + 4)
