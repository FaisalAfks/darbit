"""Actions in darbit Studio: list, read, save, breakpoints and Play (decision 0013, round 8).

A bot's actions are `actions/<name>.py` files (runs/flowfile.py). Play runs one in this process with the bot's
darbit settings, so its target names resolve to the bot's pictures, and sends `action.line` as each line runs,
`action.paused` at a breakpoint or step, and `action.ended` at the end. Breakpoints live in the bot's
`.darbit/state/breakpoints.json`, never in the file.
"""

import json
from pathlib import Path

from .. import __version__, paths
from ..project import manifest
from ..project.manifest import load
from ..runs import flowfile
from ..runs.flowfile import Section
from ..runs.player import Player
from ..settings import settings
from .events import publish

_player: Player | None = None


def _folder(project: Path) -> Path:
    return project / "actions"


def _breakpoints_file(project: Path) -> Path:
    return paths.project_dir(project) / "state" / "breakpoints.json"


def breakpoints(project: Path) -> dict[str, list[int]]:
    path = _breakpoints_file(project)
    if not path.is_file():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    if isinstance(data, dict):
        return data
    return {}


def listing(project: Path) -> list[dict]:
    """Every action with how big it is and which actions use it."""
    folder = _folder(project)
    if not folder.is_dir():
        return []
    flows = {}
    problems = {}
    for path in sorted(folder.glob("*.py")):
        if path.name == "__init__.py":
            continue
        try:
            flows[path.stem] = flowfile.read(path)
        except (flowfile.FlowError, OSError) as error:
            problems[path.stem] = str(error)
    found = []
    for name, flow in flows.items():
        steps = 0
        for section in flow.sections:
            steps += _count(section.steps)
        found.append({"name": name, "steps": steps, "sections": len(flow.sections), "used_by": _used_by(flows, name)})
    for name, problem in problems.items():
        found.append({"name": name, "steps": 0, "sections": 0, "used_by": [], "error": problem})
    found.sort(key=_by_name)
    return found


def _by_name(entry: dict) -> str:
    return entry["name"]


def _count(steps: list) -> int:
    total = 0
    for step in steps:
        total += 1 + _count(step.children)
    return total


def _used_by(flows: dict, name: str) -> list[str]:
    users = []
    for other, flow in flows.items():
        if name in flow.calls:
            users.append(other)
    return users


def read(project: Path, name: str) -> dict:
    """One action as the editor shows it."""
    path = _folder(project) / f"{name}.py"
    flow = flowfile.read(path)
    sections = []
    for section in flow.sections:
        steps = []
        for step in section.steps:
            steps.append(flowfile.to_dict(step))
        sections.append({"name": section.name, "line": section.line, "steps": steps})
    others = {}
    for other in _folder(project).glob("*.py"):
        if other.name != "__init__.py" and other.stem != name:
            try:
                others[other.stem] = flowfile.read(other)
            except (flowfile.FlowError, OSError):
                continue
    others[name] = flow
    return {
        "name": name,
        "docstring": flow.docstring,
        "sections": sections,
        "calls": flow.calls,
        "used_by": _used_by(others, name),
        "breakpoints": breakpoints(project).get(name, []),
    }


def save(project: Path, name: str, sections_data: list[dict], docstring: str = "", timed: bool | None = None) -> dict:
    """Write the action from the editor's sections and steps, then read it back (lines change).

    `timed` None keeps what the file had: a recorded action stays on its recorded schedule after edits.
    """
    if not name.isidentifier():
        raise ValueError(f"{name!r} can't be an action's name: use letters, digits and _")
    folder = _folder(project)
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "__init__.py").touch()
    sections = []
    for data in sections_data:
        steps = []
        for step in data.get("steps") or []:
            steps.append(flowfile.from_dict(step))
        sections.append(Section(str(data.get("name") or ""), steps))
    known = set()
    for path in folder.glob("*.py"):
        known.add(path.stem)
    calls = []
    for section in sections:
        _calls_in(section.steps, known, calls)
    if timed is None:
        timed = False
        existing = folder / f"{name}.py"
        if existing.exists():
            try:
                timed = flowfile.read(existing).timed
            except flowfile.FlowError:
                timed = False
    text = flowfile.render(name, sections, docstring, calls, timed)
    (folder / f"{name}.py").write_text(text, encoding="utf-8", newline="\n")
    return read(project, name)


def _calls_in(steps: list, known: set[str], found: list[str]) -> None:
    for step in steps:
        if step.kind == "call" and step.args.get("name") in known and step.args["name"] not in found:
            found.append(step.args["name"])
        _calls_in(step.children, known, found)


def set_breakpoints(project: Path, name: str, lines: list[int]) -> dict:
    found = breakpoints(project)
    found[name] = sorted(set(lines))
    path = _breakpoints_file(project)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(found, indent=2), encoding="utf-8")
    if _player is not None:
        _player.breakpoints[name] = set(found[name])
    return {"breakpoints": found[name]}


def play(project: Path, name: str, stepping: bool = False) -> dict:
    """Play an action in this process with the bot's settings, following its lines."""
    global _player
    if _player is not None and _player.thread is not None and _player.thread.is_alive():
        raise ValueError("an action is already playing")
    manifest.setup(settings, __version__, project)

    def on_line(action: str, line: int) -> None:
        publish("action.line", {"action": action, "line": line})

    def on_pause(action: str, line: int) -> None:
        publish("action.paused", {"action": action, "line": line})

    def on_end(status: str, reason: str) -> None:
        publish("action.ended", {"action": name, "status": status, "reason": reason})

    _player = Player(project, name, on_line, on_pause, on_end)
    for action, lines in breakpoints(project).items():
        _player.breakpoints[action] = set(lines)
    _player.stepping = stepping
    _player.start()
    return {"playing": True}


def control(what: str) -> dict:
    """Resume, step or stop the action playing."""
    if _player is None:
        return {"playing": False}
    if what == "resume":
        _player.resume()
    elif what == "step":
        _player.step()
    elif what == "stop":
        _player.stop()
    return {"playing": True}


# ---- requests


def _project(data: dict) -> Path:
    folder = Path(str(data.get("path", "")))
    load(folder)  # a bot folder, or ProjectError
    return folder


def register() -> None:
    from .app import HANDLERS

    def list_request(data: dict) -> list[dict]:
        return listing(_project(data))

    def read_request(data: dict) -> dict:
        return read(_project(data), str(data.get("name", "")))

    def save_request(data: dict) -> dict:
        return save(
            _project(data), str(data.get("name", "")), data.get("sections") or [], str(data.get("docstring") or "")
        )

    def breakpoints_request(data: dict) -> dict:
        lines = []
        for line in data.get("lines") or []:
            lines.append(int(line))
        return set_breakpoints(_project(data), str(data.get("name", "")), lines)

    def play_request(data: dict) -> dict:
        return play(_project(data), str(data.get("name", "")), bool(data.get("stepping")))

    def control_request(data: dict) -> dict:
        return control(str(data.get("what", "")))

    HANDLERS["actions.list"] = list_request
    HANDLERS["actions.read"] = read_request
    HANDLERS["actions.save"] = save_request
    HANDLERS["actions.breakpoints"] = breakpoints_request
    HANDLERS["actions.play"] = play_request
    HANDLERS["actions.control"] = control_request
