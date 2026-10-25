"""Where darbit keeps its files (docs/decisions/0006-data-folders.md).

Everything that needs a folder asks this module, so the library and darbit Studio agree:
user settings in %APPDATA%\\darbit, app data and cache in %LOCALAPPDATA%\\darbit, and a
project's own runtime files (logs, state) in its `.darbit` folder.
"""

from pathlib import Path

import platformdirs

APP = "darbit"


def config_dir() -> Path:
    """User settings: keymap, themes, Studio preferences. %APPDATA%\\darbit on Windows."""
    return Path(platformdirs.user_config_dir(APP, appauthor=False, roaming=True))


def data_dir() -> Path:
    """App data: installed bots, the local server's address, Studio state. %LOCALAPPDATA%\\darbit on Windows."""
    return Path(platformdirs.user_data_dir(APP, appauthor=False, roaming=False))


def cache_dir() -> Path:
    """Files that can be deleted any time: thumbnails, prepared frames. %LOCALAPPDATA%\\darbit\\Cache on Windows."""
    return Path(platformdirs.user_cache_dir(APP, appauthor=False))


def log_dir() -> Path:
    """The Studio's and the server's own logs. %LOCALAPPDATA%\\darbit\\Logs on Windows."""
    return Path(platformdirs.user_log_dir(APP, appauthor=False))


def bots_dir() -> Path:
    """Where installed bots live: one folder each, at a release tag (decision 0001)."""
    return data_dir() / "bots"


def project_dir(project: Path) -> Path:
    """A project's (a bot's) own runtime files: logs, state, run history. Not committed."""
    return project / ".darbit"
