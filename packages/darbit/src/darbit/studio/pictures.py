"""Pictures the service sends as data URLs (the Library's thumbnails, the Screen view's shots), written once to files
in darbit's cache and handed to QML as file URLs. A data URL in QML is copied as text with every read of the list
it's in, and again as each Image's source and cache key; a file URL is short, and QML reads a file the same way it
reads a data URL, so the pixels shown are the same.
"""

import base64
import hashlib
from pathlib import Path

from .. import paths

KINDS = {"image/png": ".png", "image/jpeg": ".jpg"}


class Pictures:
    """The pictures' files, one folder per kind ("thumbnail", "screen"), each named by its picture's hash."""

    def __init__(self, folder: Path | None = None) -> None:
        self.folder = folder if folder is not None else paths.cache_dir() / "studio-pictures"

    def take(self, entries: list[dict], field: str, kind: str) -> list[dict]:
        """`entries` with the data URL in each one's `field` swapped for its file's URL. Files of `kind` written before
        and not among these are deleted."""
        folder = self.folder / kind
        found = []
        wanted: set[Path] = set()
        for entry in entries:
            path = self._written(entry.get(field), folder)
            if path is not None:
                wanted.add(path)
                entry = {**entry, field: path.as_uri()}
            found.append(entry)
        self._forget_others(folder, wanted)
        return found

    def _written(self, value: object, folder: Path) -> Path | None:
        """The file holding a data URL's picture, written if it isn't there yet; None for anything else."""
        if not isinstance(value, str) or not value.startswith("data:") or "," not in value:
            return None
        head, data = value.split(",", 1)
        suffix = KINDS.get(head[len("data:") :].split(";")[0])
        if suffix is None:
            return None
        path = folder / (hashlib.sha1(data.encode("ascii", "replace")).hexdigest() + suffix)
        if path.is_file():
            return path
        try:
            folder.mkdir(parents=True, exist_ok=True)
            path.write_bytes(base64.b64decode(data))
        except (OSError, ValueError):
            return None
        return path

    def _forget_others(self, folder: Path, wanted: set[Path]) -> None:
        if not folder.is_dir():
            return
        for path in folder.iterdir():
            if path not in wanted:
                path.unlink(missing_ok=True)
