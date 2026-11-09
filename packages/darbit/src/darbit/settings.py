"""Defaults that scripts can change: `darbit.settings.timeout = 10`.

Layers, the last one wins: these defaults, then the project's darbit.toml (project/manifest.py),
then what the script sets, then one call's own arguments (`d.click("Play", timeout=5)`).
"""

import sys
from dataclasses import dataclass, field
from pathlib import Path


def script_folder() -> Path:
    """The running script's folder, or the current folder when there is no script (a console)."""
    main = sys.modules.get("__main__")
    path = getattr(main, "__file__", None)
    return Path(path).resolve().parent if path else Path.cwd()


def _default_images() -> list[Path]:
    return [script_folder() / "images", script_folder()]


def _default_logs() -> Path:
    return script_folder() / ".darbit" / "logs"


def _default_state() -> Path:
    return script_folder() / ".darbit" / "state"


@dataclass
class Settings:
    timeout: float = 3.0  # how long actions on a target wait for it, in seconds
    similarity: float = 0.7  # lowest score that counts as found, 0 to 1
    glide: float = 0.5  # seconds the mouse takes to move to a spot
    approach: float = 0  # pixels: a click with the mouse closer than this steps back this far first; 0 is off
    scan_rate: float = 5.0  # searches per second while waiting
    lag: float = 1.0  # a slow game or PC: every search's wait and every d.sleep is this many times longer
    images: list[Path] = field(default_factory=_default_images)
    window: str | None = None  # a window that must be in front before any input, e.g. "Game"
    stop_key: str = "ctrl+alt+q"
    logs: Path = field(default_factory=_default_logs)
    state: Path = field(default_factory=_default_state)  # where d.State files are kept
    log: bool = True  # write a log file per day into `logs`
    keep_days: int = 14  # run reports, daily logs and history older than this many days are deleted
    missing_images: str = "error"  # "error", or "skip" to treat a missing image as never found
    screenshot_after: float = 20.0  # save a screenshot when a wait this long (or longer) runs out
    match: dict = field(default_factory=dict)  # matching options for every target, e.g. {"fast": True}
    matcher: str = "template"  # which matcher finds images: darbit's own, or one from a plugin
    reader: str = "rapidocr"  # which reader reads text (d.read): darbit's own (the ocr extra), or one from a plugin
    read: dict = field(default_factory=dict)  # how to read text everywhere, e.g. {"upscale": 2} (core/reading.py)
    read_confidence: float = 0.5  # lowest confidence, 0 to 1, a read needs to count; below it d.read gives None
    read_threads: int = 4  # CPU threads a read uses; more is no faster on a PC busy with a game
    polite: float = (
        0.0  # seconds without the person's mouse or keys before the bot goes on after they use them; 0 is off
    )
    day_starts: str = "00:00"  # when the bot's day starts: "03:00" on this PC's clock, or "00:00 UTC" (days.py)
    space: str = "screen"  # "screen" pixels, or "window": targets taken in the app's window follow it when it moves
    # or changes size (rebuild plan, section 4: an option measured on the bench, never assumed)


settings = Settings()
