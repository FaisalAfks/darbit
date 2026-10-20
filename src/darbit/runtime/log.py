"""One log file per day, and screenshots when a long wait runs out."""
from __future__ import annotations

import logging
import time
from datetime import datetime

import cv2

from ..platform import screen
from ..settings import settings

logger = logging.getLogger("darbit")
_day = ""
_KEEP_SHOTS = 200


def _handler() -> None:
    global _day
    today = datetime.now().strftime("%Y-%m-%d")
    if today == _day:
        return
    for old in list(logger.handlers):
        if getattr(old, "_darbit", False):
            logger.removeHandler(old)
            old.close()
    settings.logs.mkdir(parents=True, exist_ok=True)
    handler = logging.FileHandler(settings.logs / f"{today}.log", encoding="utf-8")
    handler.setFormatter(logging.Formatter("%(asctime)s %(message)s", "%H:%M:%S"))
    handler._darbit = True  # type: ignore[attr-defined]
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    _day = today


def log(message: str) -> None:
    """Write a line to today's log file."""
    if not settings.log:
        return
    try:
        _handler()
        logger.info(message)
    except OSError:
        pass


def screenshot(label: str) -> None:
    """Save the screen into logs/screenshots, keeping the newest few hundred."""
    if not settings.log:
        return
    try:
        folder = settings.logs / "screenshots"
        folder.mkdir(parents=True, exist_ok=True)
        pixels, _ = screen.grab()
        safe = "".join(c if c.isalnum() or c in "-_." else "_" for c in label)[:60]
        path = folder / f"{datetime.now():%Y-%m-%d_%H-%M-%S}_{safe}.png"
        ok, data = cv2.imencode(".png", pixels)
        if ok:
            data.tofile(str(path))
            log(f"screenshot {path.name}")
        shots = sorted(folder.glob("*.png"), key=lambda p: p.stat().st_mtime)
        for old in shots[:-_KEEP_SHOTS]:
            old.unlink(missing_ok=True)
    except OSError:
        pass


def since(started: float) -> str:
    return f"{time.monotonic() - started:.1f}s"
