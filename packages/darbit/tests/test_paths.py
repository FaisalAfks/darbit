"""darbit's own folders, and DARBIT_HOME putting them under one."""

import os
from pathlib import Path

from darbit import paths
from darbit.server import ui_settings


def test_the_tests_never_use_the_real_folders():
    home = Path(os.environ["DARBIT_HOME"])
    for folder in (paths.config_dir(), paths.data_dir(), paths.cache_dir(), paths.log_dir()):
        assert folder.is_relative_to(home)


def test_darbit_home_holds_all_four(monkeypatch, tmp_path):
    monkeypatch.setenv("DARBIT_HOME", str(tmp_path))
    assert paths.config_dir() == tmp_path / "config"
    assert paths.data_dir() == tmp_path / "data"
    assert paths.bots_dir() == tmp_path / "data" / "bots"
    monkeypatch.delenv("DARBIT_HOME")
    assert paths.config_dir().name == "darbit"


def test_settings_saved_with_a_byte_order_mark_are_read(monkeypatch, tmp_path):
    monkeypatch.setenv("DARBIT_HOME", str(tmp_path))
    paths.config_dir().mkdir(parents=True)
    (paths.config_dir() / "ui.json").write_bytes(b'\xef\xbb\xbf{"studio.ghost": false}')
    assert ui_settings.get("studio.ghost") is False
