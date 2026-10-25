"""Every message between the local server and the windows, the hub and the IDE extension.

Text frames are JSON: {"type": "...", "id": 7, "data": {...}}. A message with an id is a
request and gets one {"type": "reply", "id": 7, "data": ..., "error": null}; without an id
it's an event. Images go in binary frames (see docs/tasks/T05-local-server.md).

This list is the contract. The TypeScript side is generated from it:
    python -m darbit.server.protocol --ts > packages/ui/src/lib/protocol.ts
"""

from __future__ import annotations

import sys

# type -> (who sends it, fields, what it does). "req" = request with a reply, "evt" = event.
MESSAGES: dict[str, tuple[str, dict[str, str], str]] = {
    # T05 server
    "ping": ("req", {}, "is the server there"),
    "keymap.get": ("req", {}, "the merged keymap"),
    "keymap.changed": ("evt", {"keys": "Keymap"}, "the keymap was edited"),
    "theme.get": ("req", {}, "the theme name and custom tokens"),
    "theme.changed": ("evt", {"name": "str", "tokens": "dict | None"}, "every window switches"),
    "settings.get": ("req", {"key": "str"}, "a UI setting"),
    "settings.set": ("req", {"key": "str", "value": "any"}, "save a UI setting"),
    "log": ("evt", {"line": "str"}, "a log line from a running script"),
    "record": ("evt", {"event": "str", "fields": "dict"}, "a run report event (steps, searches)"),
    # T09/T10 capture
    "capture.freeze": ("req", {"monitors": "list[int] | None"}, "grab and send frames, then lines"),
    "capture.lines": ("evt", {"monitor": "int", "lines": "Lines"}, "snap lines for a frozen frame"),
    "capture.candidates": ("req", {"x": "int", "y": "int", "kind": "Kind"}, "boxes around a point, smallest first"),
    "capture.targets": ("req", {}, "the project's saved targets"),
    "capture.save": ("req", {"draft": "Draft"}, "write the target's files"),
    "capture.undo": ("req", {}, "undo the last save, rename or delete"),
    "capture.redo": ("req", {}, "redo it"),
    "capture.rename": ("req", {"from": "str", "to": "str"}, "rename a target's files and links"),
    "capture.delete": ("req", {"name": "str"}, "delete a target's files"),
    # T11 highlight
    "highlight.scan": ("req", {"targets": "list[str] | None", "context": "str | None"}, "start a scan"),
    "highlight.hit": (
        "evt",
        {"name": "str", "box": "Box", "score": "float", "elsewhere": "float", "verdict": "str"},
        "one target found",
    ),
    "highlight.done": ("evt", {"missing": "list[str]"}, "the scan finished"),
    # T12 guide
    "guide.open": ("req", {"path": "str", "say": "str | None", "only": "list[str] | None"}, "show the guide card"),
    "guide.progress": ("evt", {"done": "int", "total": "int", "current": "str | None"}, "guide progress"),
    # T15 recorder
    "record.start": ("req", {"name": "str", "window": "str"}, "start recording"),
    "record.mark": ("req", {}, "add a checkpoint"),
    "record.pause": ("req", {}, "pause or resume recording"),
    "record.stop": ("req", {}, "stop and save"),
    "record.tick": ("evt", {"seconds": "float", "checkpoints": "int", "paused": "bool"}, "the bar's clock"),
    # T16 player and run panel
    "run.load": ("req", {"path": "str"}, "the run's tree"),
    "run.control": ("req", {"do": "continue | stop | step | pause"}, "drive the player"),
    "run.edit": ("req", {"at": "list[int]", "step": "dict"}, "change, add or remove a step"),
    "run.at": ("evt", {"checkpoint": "int", "goal": "int", "step": "int"}, "the step being played"),
    "run.paused": ("evt", {"reason": "str"}, "stopped at a breakpoint or by pause"),
    # T20 hub
    "projects.list": ("req", {}, "installed bots"),
    "project.run": ("req", {"name": "str"}, "start a bot"),
    "project.pause": ("req", {"name": "str"}, "pause or resume a bot"),
    "project.stop": ("req", {"name": "str"}, "stop a bot"),
    "project.status": ("evt", {"name": "str", "status": "str", "step": "str | None"}, "a bot's state changed"),
    "library.list": ("req", {"project": "str"}, "targets with thumbnails and last scores"),
    "reports.days": ("req", {"project": "str"}, "days with a run report"),
    "reports.day": ("req", {"project": "str", "day": "str"}, "one day's summary"),
}


def typescript() -> str:
    """The message names as a TypeScript union, for packages/ui/src/lib/protocol.ts."""
    raise NotImplementedError("TODO(T05): generate types for every message and its fields")


if __name__ == "__main__":
    if "--ts" in sys.argv:
        print(typescript())
    else:
        for name, (kind, fields, does) in MESSAGES.items():
            print(f"{kind}  {name:22} {does}")
