"""The recording that's on, for the service: the input worker writes `recording.json` in darbit's data folder (its
pid, the bot's folder and the action's name) when a recording starts and takes it away when it stops, so the service
refuses to start a bot that sends input during it (decision 0020). A file left by a worker that's gone counts for
nothing.
"""

import json
import os
from dataclasses import dataclass
from pathlib import Path

from .. import paths
from ..platform import system


@dataclass(frozen=True)
class Mark:
    project: Path
    name: str


def _file() -> Path:
    return paths.data_dir() / "recording.json"


def write(project: Path, name: str) -> None:
    """Say a recording into `project`'s actions/<name>.py is on, in this process."""
    data = {"pid": os.getpid(), "path": str(project), "name": name}
    path = _file()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data), encoding="utf-8")


def clear() -> None:
    _file().unlink(missing_ok=True)


def current() -> Mark | None:
    """The recording that's on, or None: no file, one that can't be read, or its worker is gone."""
    try:
        data = json.loads(_file().read_text(encoding="utf-8"))
        pid = int(data["pid"])
        mark = Mark(Path(str(data["path"])), str(data["name"]))
    except (OSError, ValueError, KeyError, TypeError):
        return None
    if not system.process_alive(pid):
        return None
    return mark
