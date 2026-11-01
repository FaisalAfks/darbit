"""Saving captures, and taking them back."""

from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

from ..core.geometry import Region
from ..core.targets import save
from ..platform import screen
from .common import Item, Result, distinct

RISKY = 0.7


@dataclass
class Saved:
    """One saved capture, with what its files held before, so it can be undone."""

    item: Item
    message: str
    before: dict[Path, bytes | None] = field(default_factory=dict)
    thumb: np.ndarray | None = None
    elsewhere: float | None = None

    @property
    def risky(self) -> bool:
        return self.elsewhere is not None and self.elsewhere >= RISKY


def _files(path: Path, kind: str) -> list[Path]:
    json = path.with_name(path.name + ".json")
    return [json] if kind != "image" else [path.with_name(path.name + ".png"), json]


def _backup(files: list[Path]) -> dict[Path, bytes | None]:
    return {f: f.read_bytes() if f.is_file() else None for f in files}


def undo(saved: Saved) -> None:
    """Put the files back the way they were before this capture."""
    for path, old in saved.before.items():
        if old is None:
            path.unlink(missing_ok=True)
        else:
            path.write_bytes(old)


def save_result(
    folder: Path, item: Item, result: Result, shot: np.ndarray, origin: Region, window: Region | None
) -> Saved:
    """Save a captured target. With the app's `window` area, its size and corner are saved too, so the target
    follows the window when it moves or changes size (core/placement.py)."""
    path = folder / item.name
    before = _backup(_files(path, item.kind))
    window_size = None
    window_corner = None
    if window is not None:
        window_size = [window.w, window.h]
        window_corner = [window.x, window.y]
    if item.kind == "location":
        p = result.point
        save(path, None, kind="location", location=[round(p.x), round(p.y)], window=window_size, origin=window_corner)
        return Saved(item, f"saved {path}.json: location {round(p.x)},{round(p.y)}", before)
    if item.kind == "region":
        r = result.region
        save(path, None, kind="region", region=[r.x, r.y, r.w, r.h], window=window_size, origin=window_corner)
        return Saved(item, f"saved {path}.json: region {r.x},{r.y},{r.w},{r.h}", before)
    box = result.image
    image = shot[box.y - origin.y : box.bottom - origin.y, box.x - origin.x : box.right - origin.x].copy()
    offset = None
    if result.point is not None:
        center = box.center
        offset = [round(result.point.x - center.x), round(result.point.y - center.y)]
    region = [result.region.x, result.region.y, result.region.w, result.region.h] if result.region else None
    if result.region_name:
        region = result.region_name
    scale = screen.scale_at(box.x, box.y)
    save(path, image, kind="image", region=region, offset=offset, scale=scale, window=window_size, origin=window_corner)
    elsewhere = distinct(image, shot, Region(box.x - origin.x, box.y - origin.y, box.w, box.h))
    verdict = "distinct" if elsewhere < RISKY else "RISKY, something else looks alike"
    message = (
        f"saved {path}.png ({box.w}x{box.h} at {box.x},{box.y})"
        + (f", region {region}" if region else "")
        + (f", click offset {offset}" if offset else "")
        + f"; {verdict} (best elsewhere {elsewhere:.2f})"
    )
    return Saved(item, message, before, image, elsewhere)
