"""Capture in darbit Studio: the frozen screen in its own full-screen window, boxed, tested and saved.

The work is capture/service.py's; this hands it to QML. The shot never leaves the Studio's process: QML shows
it through an image provider (`image://capture/shot`), so a 4K screen isn't copied anywhere.
"""

from pathlib import Path

import numpy as np
from PySide6.QtCore import Property, QObject, QSize, Signal, Slot
from PySide6.QtGui import QImage
from PySide6.QtQuick import QQuickImageProvider

from ..capture import service
from ..project.manifest import load


class ShotProvider(QQuickImageProvider):
    """The frozen shot, for QML's Image."""

    def __init__(self) -> None:
        super().__init__(QQuickImageProvider.ImageType.Image)
        self.image = QImage()

    def set_pixels(self, pixels: np.ndarray) -> None:
        height, width = pixels.shape[:2]
        rgb = np.ascontiguousarray(pixels[:, :, ::-1])  # OpenCV's BGR as Qt's RGB
        self.image = QImage(rgb.data, width, height, width * 3, QImage.Format.Format_RGB888).copy()

    def requestImage(self, name: str, size: QSize, wanted: QSize) -> QImage:
        return self.image


class Capture(QObject):
    """One capture session for QML: open, click for boxes, test, save, close."""

    openChanged = Signal()
    itemsChanged = Signal()
    shotChanged = Signal()
    saved = Signal(str)

    def __init__(self, provider: ShotProvider) -> None:
        super().__init__()
        self.provider = provider
        self._open = False
        self._items: list[dict] = []
        self._size = (0, 0)
        self._shot_number = 0

    def _get_open(self) -> bool:
        return self._open

    def _get_items(self) -> list:
        return self._items

    def _get_width(self) -> int:
        return self._size[0]

    def _get_height(self) -> int:
        return self._size[1]

    def _get_source(self) -> str:
        return f"image://capture/shot{self._shot_number}" if self._open else ""

    isOpen = Property(bool, _get_open, notify=openChanged)
    items = Property(list, _get_items, notify=itemsChanged)
    shotWidth = Property(int, _get_width, notify=shotChanged)
    shotHeight = Property(int, _get_height, notify=shotChanged)
    source = Property(str, _get_source, notify=shotChanged)

    def start(
        self, folder: Path, mode: str = "any", name: str = "", kind: str = "image", shot: np.ndarray | None = None
    ) -> None:
        """Open a session for the bot at `folder` on the screen now (or a saved `shot`)."""
        project = load(folder)
        images = folder / (project.images[0] if project.images else "images")
        images.mkdir(parents=True, exist_ok=True)
        started = service.start(folder, images, service.items_for(folder, mode, name, kind))
        if shot is None:
            pixels, _ = service.freeze()
        else:
            service.use_shot(shot)
            pixels = shot
        self.provider.set_pixels(pixels)
        self._size = (pixels.shape[1], pixels.shape[0])
        self._shot_number += 1
        self._items = started["items"]
        self._open = True
        self.shotChanged.emit()
        self.itemsChanged.emit()
        self.openChanged.emit()

    @Slot(int, int, str, result="QVariantMap")
    def candidates(self, x: int, y: int, kind: str) -> dict:
        """Boxes around a click, smallest first, and which one to start with."""
        try:
            return service.candidates(x, y, kind)
        except service.CaptureError:
            return {"boxes": [], "start": 0}

    @Slot(int, int, result=str)
    def colour(self, x: int, y: int) -> str:
        """The colour of the shot at (x, y), as #rrggbb, for the magnifier."""
        image = self.provider.image
        if image.isNull() or not (0 <= x < image.width() and 0 <= y < image.height()):
            return ""
        return image.pixelColor(x, y).name()

    @Slot(str, result="QVariantMap")
    def existing(self, name: str) -> dict:
        """What a target called `name` already has (area, point, picture file), for a retake to keep."""
        try:
            found = service.existing(name.strip())
        except service.CaptureError:
            return {}
        if found["picture"]:
            found["picture"] = Path(found["picture"]).as_uri()
        return found

    @Slot("QVariantList", "QVariant", result="QVariantMap")
    def test(self, box: list, region: object) -> dict:
        """Every place the boxed picture is found (in `region`, else the whole shot), with scores."""
        try:
            return service.test([int(value) for value in box], None, _box_or_none(region), 0.9)
        except service.CaptureError as error:
            return {"matches": [], "error": str(error)}

    @Slot(result="QVariantList")
    def regions(self) -> list:
        """The bot's regions to search a new image in: shared region targets, then other images' own."""
        try:
            return service.regions()
        except service.CaptureError:
            return []

    @Slot(str, str, "QVariant", "QVariant", "QVariant", str, result="QVariantMap")
    def save(self, name: str, kind: str, image: object, region: object, point: object, region_name: str = "") -> dict:
        """Write the target's files (the image searched in the shared region `region_name`, if one was picked); the
        message to show, and what's left to take."""
        try:
            result = service.save(
                name.strip(), kind, _box_or_none(image), _box_or_none(region), _point_or_none(point), region_name
            )
        except (service.CaptureError, OSError) as error:
            return {"error": str(error)}
        self._items = result["items"]
        self.itemsChanged.emit()
        self.saved.emit(name)
        return result

    @Slot()
    def close(self) -> None:
        service.stop()
        self._open = False
        self.provider.image = QImage()
        self.openChanged.emit()
        self.shotChanged.emit()


def _box_or_none(value: object) -> list[int] | None:
    if not isinstance(value, (list, tuple)) or len(value) != 4:
        return None
    return [int(part) for part in value]


def _point_or_none(value: object) -> list[float] | None:
    if not isinstance(value, (list, tuple)) or len(value) != 2:
        return None
    return [float(part) for part in value]
