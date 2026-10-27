"""Every message between the local server and the windows, the hub and the IDE extension.

Text frames are JSON: {"type": "...", "id": 7, "data": {...}}. A message with an id is a
request and gets one {"type": "reply", "id": 7, "data": ..., "error": null}; without an id
it's an event. Images go in binary frames (see docs/tasks/T05-local-server.md).

This list is the contract. The TypeScript side is generated from it:
    python -m darbit.server.protocol --ts > packages/ui/src/lib/protocol.ts
"""

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
    "log": ("evt", {"line": "str", "time": "str"}, "a log line from a running script"),
    "record": ("evt", {"event": "str", "fields": "dict"}, "a run report event (steps, searches)"),
    # T09/T10 capture (decision 0013, round 7): a session for one bot, on one frozen shot
    "capture.open": (
        "req",
        {"path": "str", "mode": "str", "name": "str | None", "kind": "Kind | None"},
        "hide the Studio, freeze, show Capture",
    ),
    "capture.session": ("req", {}, "the items still to take"),
    "capture.frame": ("req", {}, "the frozen shot as a frame"),
    "capture.candidates": ("req", {"x": "int", "y": "int", "kind": "Kind"}, "boxes around a point, smallest first"),
    "capture.test": (
        "req",
        {"box": "Box | None", "name": "str | None", "region": "Box | None", "similarity": "float"},
        "every match in the region, with scores",
    ),
    "capture.save": (
        "req",
        {"name": "str", "kind": "Kind", "image": "Box | None", "region": "Box | None", "point": "list[float] | None"},
        "write the target's files",
    ),
    "capture.close": ("req", {}, "leave Capture and show the Studio"),
    "capture.next": ("req", {}, "hide Capture until the next guide screen is frozen"),
    "capture.refreeze": ("req", {}, "grab the screen again"),
    "capture.frozen": ("evt", {}, "a new shot is ready"),
    "capture.waiting": ("evt", {}, "the bar between guide items is showing again"),
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
    # T15 recorder (decision 0013, round 8)
    "record.start": ("req", {"path": "str", "name": "str"}, "hide the Studio and record into actions/<name>.py"),
    "record.pause": ("req", {}, "pause or go on"),
    "record.check": (
        "req",
        {
            "kind": "str",
            "seconds": "float | None",
            "target": "str | None",
            "gone": "bool | None",
            "timeout": "float | None",
        },
        "while paused: add a wait or a picture check",
    ),
    "record.undo": ("req", {}, "forget the last thing recorded"),
    "record.stop": ("req", {"keep": "bool | None"}, "stop; keep writes the action"),
    "record.status": ("req", {}, "time, counts and the last steps"),
    "record.size": ("req", {"open": "bool"}, "make the recorder bar taller for its panel, or back"),
    "record.tick": ("evt", {"recording": "bool"}, "the recording's time, counts and last steps"),
    # T16 player and run panel
    "actions.list": ("req", {"path": "str"}, "the bot's actions, with their size and who uses them"),
    "actions.read": ("req", {"path": "str", "name": "str"}, "an action's sections and steps"),
    "actions.save": (
        "req",
        {"path": "str", "name": "str", "sections": "list[dict]", "docstring": "str | None"},
        "write an action",
    ),
    "actions.breakpoints": ("req", {"path": "str", "name": "str", "lines": "list[int]"}, "an action's breakpoints"),
    "actions.play": (
        "req",
        {"path": "str", "name": "str", "stepping": "bool | None"},
        "play an action, following its lines",
    ),
    "actions.control": ("req", {"what": "str"}, "resume, step or stop the action playing"),
    "action.line": ("evt", {"action": "str", "line": "int"}, "the line an action is on"),
    "action.paused": ("evt", {"action": "str", "line": "int"}, "stopped at a breakpoint or a step"),
    "action.ended": ("evt", {"action": "str", "status": "str", "reason": "str"}, "done, stopped or failed"),
    "run.load": ("req", {"path": "str"}, "the run's tree"),
    "run.control": ("req", {"do": "continue | stop | step | pause"}, "drive the player"),
    "run.edit": ("req", {"at": "list[int]", "step": "dict"}, "change, add or remove a step"),
    "run.at": ("evt", {"checkpoint": "int", "goal": "int", "step": "int"}, "the step being played"),
    "run.paused": ("evt", {"reason": "str"}, "stopped at a breakpoint or by pause"),
    # T20 Studio: a bot is named by its project folder
    "projects.list": ("req", {}, "installed bots and added project folders"),
    "project.add": ("req", {"path": "str"}, "add a project folder"),
    "project.run": ("req", {"path": "str"}, "start a bot"),
    "project.pause": ("req", {"path": "str"}, "pause or resume a bot"),
    "project.stop": ("req", {"path": "str"}, "stop a bot"),
    "project.status": ("evt", {"path": "str", "status": "str", "code": "int | None"}, "a bot started, paused or ended"),
    "project.changed": ("evt", {"path": "str"}, "a running bot's report changed"),
    "dashboard.tiles": ("req", {"path": "str", "day": "str | None"}, "a bot's Overview tiles"),
    "project.settings": ("req", {"path": "str"}, "a bot's settings form and values"),
    "project.settings.save": ("req", {"path": "str", "values": "dict"}, "save a bot's settings"),
    "library.list": ("req", {"path": "str"}, "pictures with thumbnails and last scores"),
    "library.uses": ("req", {"path": "str", "name": "str"}, "every line in the bot that names an asset"),
    "library.rename.plan": ("req", {"path": "str", "name": "str", "to": "str"}, "what renaming an asset would change"),
    "library.rename": ("req", {"path": "str", "name": "str", "to": "str"}, "rename an asset and every line naming it"),
    "results.days": ("req", {"path": "str"}, "the Results page's days, each with its lead gain"),
    "results.day": ("req", {"path": "str", "day": "str | None"}, "one day of the Results page"),
    "tools.open": ("req", {"path": "str", "tool": "str"}, "open capture, guide or check for a bot"),
    "studio.collapse": ("req", {"path": "str"}, "hide the Studio behind the run pill while the bot runs"),
    "studio.expand": ("req", {}, "bring the Studio back from the run pill"),
    "studio.page": ("evt", {"page": "str"}, "the tray asks the Studio to show a page (studio-settings)"),
}


# the named types used in MESSAGES, as TypeScript
NAMED = {
    "Keymap": "Record<string, Record<string, string>>",
    "Kind": '"image" | "region" | "point"',
    "Box": "{ x: number; y: number; w: number; h: number }",
    "Lines": "{ h: [number, number, number][]; v: [number, number, number][] }",
    "Draft": "Record<string, unknown>",
}
SIMPLE = {"str": "string", "int": "number", "float": "number", "bool": "boolean", "dict": "Record<string, unknown>"}


def ts_type(text: str) -> str:
    """A field's type from MESSAGES in TypeScript: "list[int] | None" -> "number[] | null"."""
    parts = []
    for part in text.split("|"):
        part = part.strip()
        if part.startswith("list[") and part.endswith("]"):
            parts.append(f"{ts_type(part[5:-1])}[]")
        elif part in SIMPLE:
            parts.append(SIMPLE[part])
        elif part == "None":
            parts.append("null")
        elif part == "any":
            parts.append("unknown")
        elif part in NAMED:
            parts.append(part)
        else:
            parts.append(f'"{part}"')  # a word that's one of the values: "continue | stop"
    return " | ".join(parts)


def _fields(fields: dict[str, str]) -> str:
    if not fields:
        return "Record<string, never>"
    inside = []
    for name, kind in fields.items():
        inside.append(f"{name}: {ts_type(kind)}")
    return "{ " + "; ".join(inside) + " }"


def typescript() -> str:
    """Every message and its fields as TypeScript, for packages/ui/src/lib/protocol.ts."""
    lines = [
        "// Generated from packages/darbit/src/darbit/server/protocol.py; don't edit by hand:",
        "//   uv run python -m darbit.server.protocol --ts > packages/ui/src/lib/protocol.ts",
        "",
    ]
    for name, kind in NAMED.items():
        lines.append(f"export type {name} = {kind};")
    for group, wanted in (("Requests", "req"), ("Events", "evt")):
        lines += ["", f"export interface {group} {{"]
        for name, (kind, fields, does) in MESSAGES.items():
            if kind == wanted:
                lines.append(f"  /** {does} */")
                lines.append(f'  "{name}": {_fields(fields)};')
        lines.append("}")
    lines += ["", "export type RequestType = keyof Requests;", "export type EventType = keyof Events;", ""]
    return "\n".join(lines)


if __name__ == "__main__":
    if "--ts" in sys.argv:
        print(typescript())
    else:
        for name, (kind, fields, does) in MESSAGES.items():
            print(f"{kind}  {name:22} {does}")
