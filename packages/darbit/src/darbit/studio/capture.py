"""Capture in darbit Studio: the frozen screen in its own full-screen window, boxed, tested and saved.

The work is capture/service.py's; this hands it to QML. The shot never leaves the Studio's process: QML shows
it through an image provider (`image://capture/shot`), so a 4K screen isn't copied anywhere.
"""

import json
from dataclasses import dataclass
from pathlib import Path

import cv2
import numpy as np
from PySide6.QtCore import Property, QObject, QRect, QSize, Signal, Slot
from PySide6.QtGui import QImage
from PySide6.QtQuick import QQuickImageProvider

from ..capture import service
from ..core.geometry import Region
from ..platform import screen
from ..project.manifest import load

LOSSLESS = (".png", ".bmp")


@dataclass
class SavedShot:
    """A saved screenshot cut to the main screen, as Capture works on it: its pixels, where they sat on the desktop,
    and whether they went through JPEG (a little softer than the screen)."""

    pixels: np.ndarray
    origin: Region
    lossy: bool
    shot_id: str = ""  # a screen's last shot from Capture names its shot, so the boxes placed on it stay


def shot_id_beside(path: Path) -> str:
    """The shot a screen's last shot is (its .json beside it, from Capture), or "" for any other screenshot."""
    try:
        places = json.loads(path.with_suffix(".json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return ""
    return str(places.get("shot", "")) if isinstance(places, dict) else ""


def saved_shot(path: Path) -> SavedShot | None:
    """A saved screenshot (a failure's, Scout's or a screen's last shot) for Capture, at its own pixels: the whole
    desktop is cut to the main screen, a shot of the main screen is used as it is. A lossless copy beside a JPEG
    (same name, .png) is used in its place. None when it can't be read or the screens aren't laid out as they were."""
    for twin in (path.with_suffix(suffix) for suffix in LOSSLESS):
        if path.suffix.lower() not in LOSSLESS and twin.is_file():
            path = twin
            break
    try:
        pixels = cv2.imdecode(np.fromfile(path, np.uint8), cv2.IMREAD_COLOR)  # imread can't open every Windows path
    except (OSError, cv2.error):
        return None
    if pixels is None:
        return None
    lossy = path.suffix.lower() not in LOSSLESS
    desktop = screen.desktop()
    main = screen.monitors()[0]
    if pixels.shape[:2] == (main.h, main.w):
        return SavedShot(np.ascontiguousarray(pixels), main, lossy, shot_id_beside(path))
    if pixels.shape[:2] != (desktop.h, desktop.w):
        return None
    left = main.x - desktop.x
    top = main.y - desktop.y
    return SavedShot(np.ascontiguousarray(pixels[top : top + main.h, left : left + main.w]), main, lossy)


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
        """The shot, or a part of it for a tile: "shot3/x,y,w,h" in the shot's pixels."""
        if "/" not in name:
            return self.image
        part = name.split("/", 1)[1].split(",")
        try:
            x, y, w, h = (round(float(value)) for value in part)
        except ValueError:
            return QImage()
        return self.image.copy(QRect(x, y, max(1, w), max(1, h)))


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
        self._several = False
        self._note = ""

    def _get_open(self) -> bool:
        return self._open

    def _get_items(self) -> list:
        return self._items

    def _get_width(self) -> int:
        return self._size[0]

    def _get_height(self) -> int:
        return self._size[1]

    def _get_several(self) -> bool:
        return self._several

    def _get_source(self) -> str:
        return f"image://capture/shot{self._shot_number}" if self._open else ""

    def _get_note(self) -> str:
        return self._note

    isOpen = Property(bool, _get_open, notify=openChanged)
    items = Property(list, _get_items, notify=itemsChanged)
    shotWidth = Property(int, _get_width, notify=shotChanged)
    shotHeight = Property(int, _get_height, notify=shotChanged)
    source = Property(str, _get_source, notify=shotChanged)
    several = Property(bool, _get_several, notify=openChanged)  # several new targets on this shot, not one
    shotNote = Property(str, _get_note, notify=shotChanged)  # what the shot is, when it isn't the screen now

    def start(
        self,
        folder: Path,
        mode: str = "any",
        name: str = "",
        kind: str = "image",
        shot: np.ndarray | None = None,
        origin: Region | None = None,
        lossy: bool = False,
        shot_id: str = "",
        several: bool = True,
    ) -> None:
        """Open a session for the bot at `folder` on the screen now (or a saved `shot`, sitting at `origin` on the
        desktop; `lossy` when it went through JPEG). Taking new targets ("any") takes as many as are boxed on the shot,
        unless `several` is off; a retake ("one") and the guide take one at a time."""
        project = load(folder)
        images = folder / (project.images[0] if project.images else "images")
        images.mkdir(parents=True, exist_ok=True)
        started = service.start(folder, images, service.items_for(folder, mode, name, kind), retake=mode == "one")
        if shot is None:
            pixels, _ = service.freeze()
            self._note = ""
        else:
            self._note = "On a saved shot (JPEG: a little softer than the screen)" if lossy else "On a saved shot"
            service.use_shot(shot, origin, shot_id)
            pixels = shot
        self.provider.set_pixels(pixels)
        self._size = (pixels.shape[1], pixels.shape[0])
        self._shot_number += 1
        self._items = started["items"]
        self._several = several and mode == "any"
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
        self._note = ""
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
