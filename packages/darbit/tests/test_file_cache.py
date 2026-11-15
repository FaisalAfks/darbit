"""The Overview keeps what it works out from folders until they change (#498)."""

import os
import time

from darbit.server import file_cache, history, overview
from darbit.server.file_cache import FileCache


def test_a_result_is_kept_until_its_folder_changes(tmp_path):
    cache, worked = FileCache(), []

    def work():
        worked.append(1)
        return len(list(tmp_path.iterdir()))

    assert cache.get("k", [tmp_path], work) == 0
    assert cache.get("k", [tmp_path], work) == 0
    assert len(worked) == 1  # the folder didn't change: kept
    (tmp_path / "a.jpg").write_bytes(b"x")
    os.utime(tmp_path, ns=(time.time_ns(), time.time_ns() + 1_000_000))  # some file systems round the folder's time
    assert cache.get("k", [tmp_path], work) == 1
    assert len(worked) == 2


def test_a_kept_result_is_worked_out_again_after_max_age(tmp_path, monkeypatch):
    cache, worked = FileCache(), []
    clock = [1000.0]
    monkeypatch.setattr(file_cache.time, "monotonic", lambda: clock[0])
    cache.get("k", [tmp_path], lambda: worked.append(1))
    clock[0] += file_cache.MAX_AGE
    cache.get("k", [tmp_path], lambda: worked.append(1))
    assert len(worked) == 2


def test_a_missing_path_is_part_of_the_stamp(tmp_path):
    missing = tmp_path / "nope"
    assert file_cache.stamp([missing]) == (None,)
    missing.mkdir()
    assert file_cache.stamp([missing]) != (None,)


def test_the_newest_screenshot_follows_a_new_one(tmp_path):
    shots = tmp_path / "screenshots"
    shots.mkdir()
    (shots / "one.jpg").write_bytes(b"1")
    assert overview._last_screen(tmp_path).endswith("one.jpg")
    later = time.time_ns() + 5_000_000_000
    (shots / "two.jpg").write_bytes(b"2")
    os.utime(shots / "two.jpg", ns=(later, later))
    os.utime(shots, ns=(later, later))
    assert overview._last_screen(tmp_path).endswith("two.jpg")


def test_the_history_tables_are_made_once_per_file(tmp_path, monkeypatch):
    path = tmp_path / "history.sqlite"
    monkeypatch.setattr(history, "database", lambda project: path)
    monkeypatch.setattr(history, "_ready", set())
    scripts = []
    real_connect = history.sqlite3.connect

    class Watched:
        def __init__(self, connection):
            self.connection = connection

        def executescript(self, script):
            scripts.append(1)
            return self.connection.executescript(script)

        def __getattr__(self, name):
            return getattr(self.connection, name)

    monkeypatch.setattr(history.sqlite3, "connect", lambda *args, **kwargs: Watched(real_connect(*args, **kwargs)))
    for _ in range(3):
        history._open(None).close()
    assert len(scripts) == 1
    path.unlink()
    history._open(None).close()  # a new file gets its tables again
    assert len(scripts) == 2
