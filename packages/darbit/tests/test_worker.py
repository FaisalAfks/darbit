"""The input worker as its own process (python -m darbit.worker), as darbit Studio starts it."""

import pytest

from darbit.studio.worker_link import WorkerLink


def test_the_worker_answers_and_ends_with_the_studio(tmp_path):
    link = WorkerLink(lambda topic, data: None)
    try:
        assert link.call("record.status") == {"recording": False}
        with pytest.raises(ValueError, match="no method called"):
            link.call("record.fly")
        (tmp_path / "darbit.toml").write_text('[bot]\nname = "w-bot"\n', encoding="utf-8")
        try:
            link.call("record.start", path=str(tmp_path), name="run")
        except ValueError as error:
            assert "Windows" in str(error)  # no input listener on this system: said, not a crash
        else:
            link.call("record.stop", keep=False)
        assert link.process.poll() is None
    finally:
        process = link.process
        link.close()
    assert process.poll() is not None  # it ends when the Studio closes its stdin
