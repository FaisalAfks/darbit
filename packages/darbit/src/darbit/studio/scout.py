"""Scout in darbit Studio: every image of the bot searched on screen while the game is played by hand, with a record
for the session of what's been seen.

While it's on, a thread grabs the screen a couple of times a second and searches each of the bot's images in its
region (with the bot's matching options and `fast` added, so a pass stays quick but an image is still told from one in
other colours, as the bot sees it), then hands QML the boxes and scores. The overlay doesn't take clicks: they go to
the game. Each image's record says when it was last seen, its best score and on which screen, with the latest shot of
each screen (one per screen) for a retake on it: an image is seen, weak or not seen yet.
"""

import json
import threading
import time
from dataclasses import dataclass, field, replace
from pathlib import Path

import cv2
import numpy as np
from PySide6.QtCore import Property, QObject, QSize, Signal, Slot
from PySide6.QtGui import QImage
from PySide6.QtQuick import QQuickImageProvider

from .. import paths
from ..core import matching, placement
from ..core.geometry import Region
from ..core.targets import Target, kind_of, load
from ..core.targets import forget as forget_targets
from ..platform import screen
from ..platform.backend import NotSupported
from ..project.manifest import ProjectError
from ..project.manifest import load as load_project

EVERY = 0.5  # seconds between passes
SIMILARITY = 0.7  # what counts as found when neither the image nor the bot names a similarity (darbit's default)
NEAR = 0.15  # an image this far under what it needs is weak (the overlay gives it a faint box); further, not seen
SHOT_EVERY = 3.0  # seconds before a screen's shot is saved again just for a better score
SHOT_QUALITY = 85  # JPEG quality of the shots Scout keeps
SHOWN_WIDTH = 960  # px, a screen's shot is shown in the pill at most this wide
GROUPS = ("all", "weak", "not", "seen")  # the pill's filter; "all" lists the weak first, then those not seen yet


def image_files(folder: Path) -> list[Path]:
    """The image files of the bot at `folder`, in its image folders."""
    project = load_project(folder)
    found = []
    for name in project.images or ["images"]:
        images = folder / name
        if images.is_dir():
            found.extend(sorted(images.glob("*.png")))
    return found


def targets_of(folder: Path) -> list[Target]:
    """Every image of the bot at `folder`, loaded with its settings (its region, its similarity)."""
    project = load_project(folder)
    folders = [folder / name for name in (project.images or ["images"])]
    bot_similarity = float(project.settings.get("similarity", SIMILARITY))
    found = []
    for images in folders:
        if not images.is_dir():
            continue
        for path in sorted(images.glob("*.png")):
            try:
                target = load(path.stem, folders)
            except (OSError, ValueError):
                continue
            if target.similarity is None:
                target = replace(target, similarity=bot_similarity)  # what the bot itself needs
            found.append(target)
    return found


def forget_images() -> None:
    """Let go of every image's pixels darbit keeps for the next search (about 70 MB for a bot of 200 images): Scout
    is off, and the Studio doesn't search again until it's on."""
    forget_targets()
    placement.forget_resized()


def options_of(folder: Path) -> matching.Options:
    """The bot's matching options, with `fast` on (never grayscale: Scout mustn't find what the bot wouldn't)."""
    try:
        chosen = dict(load_project(folder).settings.get("match", {}))
    except ProjectError:
        chosen = {}
    chosen["fast"] = True
    return matching.Options.from_dict(chosen)


def scan(targets: list[Target], pixels: np.ndarray, origin: Region, options: matching.Options) -> list[dict]:
    """Each image's best place on this screen (screen pixels), its score and whether that counts as found."""
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
    """Images found on the same spot: each lists the others in `with`, and only the best of them is shown
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


@dataclass
class Sighting:
    """One image's record for the session: whether, when and where it was seen, and how well."""

    name: str
    needs: float
    file: str  # the image's file
    best: float = 0.0
    seen_at: float = 0.0  # time.time() it was last seen, 0 never
    times: int = 0  # passes it was seen in
    seen_on: str = ""  # the screen it was last seen on
    shot: str = ""  # that screen's saved shot, while it's still the shot this image was seen in
    box: list[int] | None = None  # where it is in the shot's pixels
    shot_version: int = 0  # how many times that shot has been saved, so the pill shows the latest
    shot_size: tuple[int, int] = (0, 0)  # the shot's width and height in pixels
    alike: list[str] = field(default_factory=list)  # images found on the same spot

    @property
    def state(self) -> str:
        """seen, weak (found under what it needs, or with a look-alike) or not seen yet ("not")."""
        if self.seen_at == 0:
            return "not"
        if self.alike or self.best < self.needs:
            return "weak"
        return "seen"

    def as_dict(self) -> dict:
        return {
            "name": self.name,
            "screen": screen_of(self.name),
            "state": self.state,
            "needs": self.needs,
            "best": self.best,
            "seenAt": self.seen_at,
            "times": self.times,
            "seenOn": self.seen_on,
            "shot": self.shot,
            "shown": f"image://scout/{Path(self.shot).stem}/{self.shot_version}" if self.shot else "",
            "box": self.box,
            "shotSize": list(self.shot_size),
            "alike": list(self.alike),
            "file": Path(self.file).as_uri() if self.file else "",
        }


@dataclass
class ScreenShot:
    """A screen's latest saved shot, and the images boxed on it."""

    path: Path
    names: set[str]
    at: float
    version: int = 1


def places_of(folder: Path) -> list[dict]:
    """The bot's Regions and Locations, each with the screen it belongs to, for Scout to show on that screen."""
    found = []
    for name in load_project(folder).images or ["images"]:
        images = folder / name
        if not images.is_dir():
            continue
        for path in sorted(images.glob("*.json")):
            if _with_suffix(path, ".png").is_file():
                continue  # an image's settings
            try:
                settings = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, ValueError):
                continue
            if not isinstance(settings, dict):
                continue
            place = _place_of(path.stem, settings)
            if place is not None:
                found.append(place)
    return found


def _with_suffix(path: Path, suffix: str) -> Path:
    return path.with_name(path.stem + suffix)


def _place_of(name: str, settings: dict) -> dict | None:
    kind = kind_of(settings, False)
    region = settings.get("region")
    location = settings.get("location")
    if kind == "region" and isinstance(region, list) and len(region) == 4:
        return {"name": name, "kind": kind, "screen": screen_of(name), "box": [int(value) for value in region]}
    if kind == "location" and isinstance(location, list) and len(location) == 2:
        x, y = (int(value) for value in location)
        return {"name": name, "kind": kind, "screen": screen_of(name), "box": [x, y, 0, 0]}
    return None


class ShownShots:
    """Each screen's latest shot, made small, for the pill to show."""

    def __init__(self) -> None:
        self.images: dict[str, QImage] = {}
        self.lock = threading.Lock()

    def keep(self, screen_name: str, pixels: np.ndarray) -> None:
        height, width = pixels.shape[:2]
        if width > SHOWN_WIDTH:
            height = round(height * SHOWN_WIDTH / width)
            width = SHOWN_WIDTH
            pixels = cv2.resize(pixels, (width, height), interpolation=cv2.INTER_AREA)
        rgb = np.ascontiguousarray(pixels[:, :, ::-1])  # OpenCV's BGR as Qt's RGB
        image = QImage(rgb.data, width, height, width * 3, QImage.Format.Format_RGB888).copy()
        with self.lock:
            self.images[screen_name] = image

    def clear(self) -> None:
        with self.lock:
            self.images = {}

    def get(self, screen_name: str) -> QImage:
        with self.lock:
            return self.images.get(screen_name, QImage())


class ShotsProvider(QQuickImageProvider):
    """Scout's shots for QML's Image: `image://scout/<screen>/<version>` (the version makes it load the latest)."""

    def __init__(self, shots: ShownShots) -> None:
        super().__init__(QQuickImageProvider.ImageType.Image)
        self.shots = shots

    def requestImage(self, name: str, size: QSize, wanted: QSize) -> QImage:
        return self.shots.get(name.split("/")[0])


def screen_of(name: str) -> str:
    """The screen an image belongs to by its name ("Shop" for "Shop.Buy"), as Capture keeps screens."""
    return name.split(".")[0] if "." in name else "Other"


def shots_folder(folder: Path) -> Path:
    """Where Scout keeps the latest shot of each screen it saw, for a retake on it."""
    return paths.project_dir(folder) / "scout"


def near_enough(box: dict) -> bool:
    """Found, or close enough under what it needs to count as weak, with a place on screen."""
    return bool(box.get("w")) and box["score"] >= box["needs"] - NEAR


def showing(boxes: list[dict]) -> str:
    """The screen showing in a pass: the one most of the images found (or nearly) belong to; "" when there's none."""
    counts: dict[str, int] = {}
    for box in boxes:
        if near_enough(box):
            name = screen_of(box["name"])
            counts[name] = counts.get(name, 0) + 1
    if not counts:
        return ""
    return max(sorted(counts), key=lambda name: counts[name])


class Scout(QObject):
    """Scout for QML: on or off, the latest pass's boxes, and the session's record of every image."""

    changed = Signal()
    recordChanged = Signal()
    _scanned = Signal(object, float)  # (the boxes, how long the pass took), from the scanning thread

    def __init__(self) -> None:
        super().__init__()
        self._on = False
        self._boxes: list[dict] = []
        self._took = 0.0
        self._origin = (0, 0)
        self._running = threading.Event()
        self._folder: Path | None = None
        self._record: dict[str, Sighting] = {}
        self._shots: dict[str, ScreenShot] = {}
        self._lock = threading.Lock()  # the record is written by the scanning thread and read by QML's
        self._landed = ""
        self._last_shown: list[tuple] = []
        self._group = "all"
        self._showing = ""
        self._present: list[str] = []
        self._places: list[dict] = []
        self.shots = ShownShots()
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

    def _get_images(self) -> list:
        with self._lock:
            return [sighting.as_dict() for sighting in self._record.values()]

    def _count(self, state: str) -> int:
        with self._lock:
            return sum(1 for sighting in self._record.values() if sighting.state == state)

    def _get_seen(self) -> int:
        return self._count("seen")

    def _get_weak(self) -> int:
        return self._count("weak")

    def _get_not_seen(self) -> int:
        return self._count("not")

    def _get_total(self) -> int:
        return len(self._record)

    def _get_landed(self) -> str:
        return self._landed

    @property
    def folder(self) -> str:
        """The bot Scout is on (or was on last), as a path."""
        return str(self._folder or "")

    def _get_group(self) -> str:
        return self._group

    def _get_listed(self) -> list:
        return [sighting.as_dict() for sighting in self._listed()]

    def _get_showing(self) -> str:
        return self._showing

    def _get_present(self) -> list:
        return self._present

    def _get_places(self) -> list:
        return self._places

    def _listed(self) -> list[Sighting]:
        """The images in the group picked, in the order the pill steps through them."""
        with self._lock:
            every = list(self._record.values())
        if self._group == "all":
            order = {"weak": 0, "not": 1, "seen": 2}
            return sorted(every, key=lambda sighting: order[sighting.state])
        return [sighting for sighting in every if sighting.state == self._group]

    isOn = Property(bool, _get_on, notify=changed)
    boxes = Property(list, _get_boxes, notify=changed)
    took = Property(float, _get_took, notify=changed)  # ms the last pass took
    found = Property(int, _get_found, notify=changed)  # found, and alone on their spot
    alike = Property(int, _get_alike, notify=changed)  # found on the same spot as another image
    origin = Property(list, _get_origin, notify=changed)  # the desktop's top left, where the overlay starts
    images = Property(list, _get_images, notify=recordChanged)  # every image's record, in name order
    seen = Property(int, _get_seen, notify=recordChanged)
    weak = Property(int, _get_weak, notify=recordChanged)
    notSeen = Property(int, _get_not_seen, notify=recordChanged)
    total = Property(int, _get_total, notify=recordChanged)
    landed = Property(str, _get_landed, notify=recordChanged)  # the image picked to look at, "" for none
    group = Property(str, _get_group, notify=recordChanged)  # all, weak, not or seen: what the pill lists
    listed = Property(list, _get_listed, notify=recordChanged)  # the images in that group, in order
    showing = Property(str, _get_showing, notify=changed)  # the screen showing now, from the images found on it
    present = Property(list, _get_present, notify=changed)  # every screen with an image found now
    places = Property(list, _get_places, notify=recordChanged)  # the bot's Regions and Locations, by screen

    def start(self, folder: Path, grab: object = None, land_on: str = "") -> None:
        """Start scouting the bot at `folder`'s images (`grab`: the screen, for tests), landed on `land_on`. The
        record goes on from before unless it's another bot."""
        self.stop()
        targets = targets_of(folder)
        files = {path.stem: path for path in image_files(folder)}
        with self._lock:
            if self._folder != folder:
                self._folder = folder
                self._shots = {}
                self._record = {}
                self.shots.clear()
            kept = self._record
            self._record = {
                target.name: kept.get(target.name) or _sighting_of(target, files.get(target.name)) for target in targets
            }
        self._landed = land_on
        self._places = places_of(folder)
        options = options_of(folder)
        self._running.set()
        self._on = True
        self.changed.emit()
        self.recordChanged.emit()
        threading.Thread(target=self._loop, args=(targets, options, grab or screen.grab), daemon=True).start()

    @Slot()
    def stop(self) -> None:
        self._running.clear()
        if self._on:
            self._on = False
            self._boxes = []
            self._showing = ""
            self._present = []
            self.changed.emit()

    @Slot()
    def reset(self) -> None:
        """Start the session's record over: every image not seen yet."""
        with self._lock:
            self._record = {
                name: Sighting(name, sighting.needs, sighting.file) for name, sighting in self._record.items()
            }
            self._shots = {}
        self.shots.clear()
        self.recordChanged.emit()

    @Slot(str)
    def forget(self, name: str) -> None:
        """Start one image's record over (it was taken again)."""
        with self._lock:
            sighting = self._record.get(name)
            if sighting is not None:
                self._record[name] = Sighting(name, sighting.needs, sighting.file)
        self.recordChanged.emit()

    @Slot(str)
    def landOn(self, name: str) -> None:
        """Pick one image to look at ("" for none)."""
        self._landed = name
        self.recordChanged.emit()

    @Slot(str)
    def setGroup(self, group: str) -> None:
        """List all the images, or only the weak ones, those not seen yet or those seen; landed on its first."""
        if group not in GROUPS:
            return
        self._group = group
        names = [sighting.name for sighting in self._listed()]
        if self._landed not in names:
            self._landed = names[0] if names else ""
        self.recordChanged.emit()

    @Slot()
    def next(self) -> None:
        """Land on the next image of the group (N)."""
        self.step(1)

    @Slot()
    def previous(self) -> None:
        """Land on the image before in the group (Shift+N)."""
        self.step(-1)

    def step(self, by: int) -> None:
        names = [sighting.name for sighting in self._listed()]
        if not names:
            return
        if self._landed in names:
            self._landed = names[(names.index(self._landed) + by) % len(names)]
        else:
            self._landed = names[0] if by > 0 else names[-1]
        self.recordChanged.emit()

    def _loop(self, targets: list[Target], options: matching.Options, grab: object) -> None:
        try:
            self._scan_while_on(targets, options, grab)
        finally:
            if not self._running.is_set():
                forget_images()

    def _scan_while_on(self, targets: list[Target], options: matching.Options, grab: object) -> None:
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
                self.note(boxes, pixels, origin)
                self._scanned.emit(boxes, (time.perf_counter() - started) * 1000)
            time.sleep(max(0.0, EVERY - (time.perf_counter() - started)))

    def note(self, boxes: list[dict], pixels: np.ndarray, origin: Region) -> None:
        """Add a pass to the record, and keep the shot of the screen showing when it's worth keeping."""
        now = time.time()
        where = showing(boxes)
        near = [box for box in boxes if near_enough(box)]
        self._showing = where
        self._present = sorted({screen_of(box["name"]) for box in near})
        better = False
        with self._lock:
            for box in near:
                sighting = self._record.get(box["name"])
                if sighting is None:
                    continue
                if sighting.seen_at == 0 or box["score"] > sighting.best:
                    better = True
                sighting.needs = box["needs"]
                sighting.best = max(sighting.best, box["score"])
                sighting.seen_at = now
                sighting.times += 1
                sighting.seen_on = where or screen_of(box["name"])
                for other in box.get("with", []):
                    if other not in sighting.alike:
                        sighting.alike.append(other)
        if near and where:
            self._keep_shot(where, near, pixels, origin, better, now)

    def _keep_shot(
        self, where: str, near: list[dict], pixels: np.ndarray, origin: Region, better: bool, now: float
    ) -> None:
        """Save the screen's shot again when an image seen now has no shot of its own yet, or (now and then) for a
        better score with every image of the shot from before still seen. One shot per screen, the latest."""
        if self._folder is None:
            return
        names = {box["name"] for box in near}
        kept = self._shots.get(where)
        with self._lock:
            unshot = [name for name in names if name in self._record and not self._record[name].shot]
        covers = kept is None or kept.names <= names
        if kept is not None and not unshot and not (covers and better and now - kept.at >= SHOT_EVERY):
            return
        path = shots_folder(self._folder) / f"{where}.jpg"
        ok, data = cv2.imencode(".jpg", pixels, [cv2.IMWRITE_JPEG_QUALITY, SHOT_QUALITY])
        if not ok:
            return
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            data.tofile(str(path))  # imwrite can't write every Windows path
        except OSError:
            return
        self.shots.keep(where, pixels)
        version = kept.version + 1 if kept is not None else 1
        with self._lock:
            if kept is not None:
                for name in kept.names - names:  # not in this screen's shot any more
                    sighting = self._record.get(name)
                    if sighting is not None and sighting.shot == str(path):
                        sighting.shot = ""
                        sighting.box = None
                        sighting.shot_size = (0, 0)
            for box in near:
                sighting = self._record.get(box["name"])
                if sighting is not None:
                    sighting.shot = str(path)
                    sighting.shot_version = version
                    sighting.shot_size = (pixels.shape[1], pixels.shape[0])
                    sighting.box = [box["x"] - origin.x, box["y"] - origin.y, box["w"], box["h"]]
        self._shots[where] = ScreenShot(path, names, now, version)

    @Slot(object, float)
    def _take(self, boxes: object, took: float) -> None:
        if self._on and isinstance(boxes, list):
            self._boxes = boxes
            self._took = took
            self.changed.emit()
            shown = self._shown()
            if shown != self._last_shown:  # the lists in the pill are built again only when what they show changed
                self._last_shown = shown
                self.recordChanged.emit()

    def _shown(self) -> list[tuple]:
        """What the pill shows of each image: its state, best score, screen, shot and look-alikes."""
        with self._lock:
            return [
                (
                    sighting.name,
                    sighting.state,
                    round(sighting.best, 2),
                    sighting.seen_on,
                    sighting.shot_version,
                    tuple(sighting.alike),
                )
                for sighting in self._record.values()
            ]


def _sighting_of(target: Target, file: Path | None) -> Sighting:
    needs = target.similarity if target.similarity is not None else SIMILARITY
    return Sighting(target.name, needs, str(file.resolve()) if file else "")
