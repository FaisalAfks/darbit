"""Defaults that scripts can change: `darbit.settings.timeout = 10`."""
from __future__ import annotations

import sys
from dataclasses import dataclass, field
from pathlib import Path


def _script_folder() -> Path:
    main = sys.modules.get("__main__")
    path = getattr(main, "__file__", None)
    return Path(path).resolve().parent if path else Path.cwd()


@dataclass
class Settings:
    timeout: float = 3.0  # how long actions on a target wait for it, in seconds
    similarity: float = 0.7  # lowest score that counts as found, 0 to 1
    glide: float = 0.5  # seconds the mouse takes to move to a spot
    scan_rate: float = 5.0  # searches per second while waiting
    images: list[Path] = field(default_factory=lambda: [_script_folder() / "images", _script_folder()])
    window: str | None = None  # a window that must be in front before any input, e.g. "Roblox"
    stop_key: str = "ctrl+alt+q"
    logs: Path = field(default_factory=lambda: _script_folder() / ".darbit" / "logs")
    state: Path = field(default_factory=lambda: _script_folder() / ".darbit" / "state")  # where d.State files are kept
    log: bool = True  # write a log file per day into `logs`
    missing_images: str = "error"  # "error", or "skip" to treat a missing image as never found
    screenshot_after: float = 20.0  # save a screenshot when a wait this long (or longer) runs out


settings = Settings()
