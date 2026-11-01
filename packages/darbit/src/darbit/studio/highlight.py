"""Highlight in darbit Studio: what's found on screen right now, with scores, over the game.

While it's on, a thread grabs the screen a couple of times a second and searches each of the bot's pictures in its
region (with the bot's matching options and `fast` added, so a pass stays quick but a picture is still told from
one in other colours, as the bot sees it), then hands QML the boxes and scores. The overlay doesn't take clicks: they go to the game.
"""

import threading
import time
from pathlib import Path

import numpy as np
from PySide6.QtCore import Property, QObject, Signal, Slot

from ..core import matching
from ..core.geometry import Region
from ..core.targets import Target, load
from ..platform import screen
from ..platform.backend import NotSupported
from ..project.manifest import ProjectError
from ..project.manifest import load as load_project

EVERY = 0.5  # seconds between passes
SIMILARITY = 0.7  # what counts as found when a picture has no similarity of its own (darbit's default)


def targets_of(folder: Path) -> list[Target]:
    """Every picture of the bot at `folder`, loaded with its settings (its region, its similarity)."""
    project = load_project(folder)
    folders = [folder / name for name in (project.images or ["images"])]
    found = []
    for images in folders:
        if not images.is_dir():
            continue
        for path in sorted(images.glob("*.png")):
            try:
                found.append(load(path.stem, folders))
            except (OSError, ValueError):
                continue
    return found


def options_of(folder: Path) -> matching.Options:
    """The bot's matching options, with `fast` on (never grayscale: Highlight mustn't find what the bot wouldn't)."""
    try:
        chosen = dict(load_project(folder).settings.get("match", {}))
    except ProjectError:
        chosen = {}
    chosen["fast"] = True
    return matching.Options.from_dict(chosen)


def scan(targets: list[Target], pixels: np.ndarray, origin: Region, options: matching.Options) -> list[dict]:
    """Each picture's best place on this screen (screen pixels), its score and whether that counts as found."""
    found = []
    for target in targets:
        area = Region(origin.x, origin.y, pixels.shape[1], pixels.shape[0])
        if target.region is not None:
            area = target.region.intersect(area) or area
        haystack = pixels[area.y - origin.y : area.bottom - origin.y, area.x - origin.x : area.right - origin.x]
        need = target.similarity if target.similarity is not None else SIMILARITY
        try:
            match = matching.closest(target, haystack, area, need, options)
        except ValueError:
            match = None
        if match is None:
            found.append({"name": target.name, "found": False, "score": 0.0, "needs": need})
            continue
        found.append(
            {
                "name": target.name,
                "found": match.score >= need,
                "score": round(float(match.score), 3),
                "needs": need,
                "x": match.x,
                "y": match.y,
                "w": match.w,
                "h": match.h,
                "region": [area.x, area.y, area.w, area.h] if target.region is not None else None,
            }
        )
    return found


SAME_SPOT = 0.7  # boxes overlapping this much (intersection over union) are the same spot


def mark_look_alikes(boxes: list[dict]) -> list[dict]:
    """Pictures found on the same spot: each lists the others in `with`, and only the best of them is shown
    (`shown`). The bot can't tell them apart there, which the `colour` option often fixes."""
    found = [box for box in boxes if box.get("found")]
    for box in boxes:
        box["with"] = []
        box["shown"] = bool(box.get("found"))
    for index, box in enumerate(found):
        for other in found[index + 1 :]:
            if _overlap(box, other) >= SAME_SPOT:
                box["with"].append(other["name"])
                other["with"].append(box["name"])
    for box in found:
        for other in found:
            if other["name"] in box["with"] and (other["score"], other["name"]) > (box["score"], box["name"]):
                box["shown"] = False  # a better one stands for the spot
    return boxes


def _overlap(a: dict, b: dict) -> float:
    width = max(0, min(a["x"] + a["w"], b["x"] + b["w"]) - max(a["x"], b["x"]))
    height = max(0, min(a["y"] + a["h"], b["y"] + b["h"]) - max(a["y"], b["y"]))
    shared = width * height
    union = a["w"] * a["h"] + b["w"] * b["h"] - shared
    return shared / union if union else 0.0


class Highlight(QObject):
    """Highlight for QML: on or off, and the latest pass's boxes."""

    changed = Signal()
    _scanned = Signal(object, float)  # (the boxes, how long the pass took), from the scanning thread

    def __init__(self) -> None:
        super().__init__()
        self._on = False
        self._boxes: list[dict] = []
        self._took = 0.0
        self._origin = (0, 0)
        self._running = threading.Event()
        self._scanned.connect(self._take)

    def _get_on(self) -> bool:
        return self._on

    def _get_boxes(self) -> list:
        return self._boxes

    def _get_took(self) -> float:
        return self._took

    def _get_found(self) -> int:
        return sum(1 for box in self._boxes if box.get("found") and not box.get("with"))

    def _get_alike(self) -> int:
        return sum(1 for box in self._boxes if box.get("found") and box.get("with"))

    def _get_origin(self) -> list:
        return list(self._origin)

    isOn = Property(bool, _get_on, notify=changed)
    boxes = Property(list, _get_boxes, notify=changed)
    took = Property(float, _get_took, notify=changed)  # ms the last pass took
    found = Property(int, _get_found, notify=changed)  # found, and alone on their spot
    alike = Property(int, _get_alike, notify=changed)  # found on the same spot as another picture
    origin = Property(list, _get_origin, notify=changed)  # the desktop's top left, where the overlay starts

    def start(self, folder: Path, grab: object = None) -> None:
        """Start highlighting the bot at `folder`'s pictures (`grab`: the screen, for tests)."""
        self.stop()
        targets = targets_of(folder)
        options = options_of(folder)
        self._running.set()
        self._on = True
        self.changed.emit()
        threading.Thread(target=self._loop, args=(targets, options, grab or screen.grab), daemon=True).start()

    @Slot()
    def stop(self) -> None:
        self._running.clear()
        if self._on:
            self._on = False
            self._boxes = []
            self.changed.emit()

    def _loop(self, targets: list[Target], options: matching.Options, grab: object) -> None:
        while self._running.is_set():
            started = time.perf_counter()
            try:
                pixels, origin = grab()
            except NotSupported:
                self._running.clear()
                return
            boxes = mark_look_alikes(scan(targets, pixels, origin, options))
            self._origin = (origin.x, origin.y)
            if self._running.is_set():
                self._scanned.emit(boxes, (time.perf_counter() - started) * 1000)
            time.sleep(max(0.0, EVERY - (time.perf_counter() - started)))

    @Slot(object, float)
    def _take(self, boxes: object, took: float) -> None:
        if self._on and isinstance(boxes, list):
            self._boxes = boxes
            self._took = took
            self.changed.emit()
