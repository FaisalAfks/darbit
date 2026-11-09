"""The last thing deleted from a bot's Library (an asset's files, or an action with its tape), kept in the bot's
.darbit/deleted so Undo can put it back. Only the last one is kept: deleting another lets the one before go.

keep() moves the files in, with a note of where each came from; take_back() moves them back and returns the note.
"""

import json
import shutil
from pathlib import Path

from .. import paths

NOTE = "deleted.json"


def _folder(project: Path) -> Path:
    return paths.project_dir(project) / "deleted"


def keep(project: Path, files: list[Path], what: dict) -> None:
    """Move `files` out of the bot into its holding folder, with `what` (the name, the kind) to put them back by."""
    folder = _folder(project)
    shutil.rmtree(folder, ignore_errors=True)
    folder.mkdir(parents=True)
    places = []
    for number, path in enumerate(files):
        kept = folder / f"{number}{path.suffix}"
        shutil.move(path, kept)
        places.append(str(path))
    note = {**what, "files": places}
    (folder / NOTE).write_text(json.dumps(note, indent=1), encoding="utf-8")


def take_back(project: Path) -> dict:
    """Put the last deleted thing's files back where they were; the note kept with them. Nothing changes when one of
    those places has a file again."""
    folder = _folder(project)
    note_file = folder / NOTE
    if not note_file.is_file():
        raise ValueError("nothing deleted to put back")
    note = json.loads(note_file.read_text(encoding="utf-8"))
    places = [Path(place) for place in note.get("files", [])]
    for place in places:
        if place.exists():
            raise ValueError(f"{place.name} is there again: {note.get('name', '')} can't be put back")
    for number, place in enumerate(places):
        place.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(folder / f"{number}{place.suffix}", place)
    shutil.rmtree(folder, ignore_errors=True)
    return note
