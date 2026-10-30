"""The built web UI (from ui/ in the repo), shipped in the wheel. See docs/archive/tasks/T01-ui-package.md."""

import os
from pathlib import Path

DEV_SERVER = "http://127.0.0.1:5173"


def static_dir() -> Path:
    return Path(__file__).with_name("static")


def app_url(app: str, port: int) -> str:
    """Where a window loads an app from: the Vite dev server with DARBIT_UI_DEV=1, else the local server."""
    if os.environ.get("DARBIT_UI_DEV"):
        return f"{DEV_SERVER}/{app}/"
    return f"http://127.0.0.1:{port}/{app}/"
