"""Actions as Python files: an `@d.flow` function, read into steps for the Studio and written back (decision 0010).

    flow = read(Path("actions/dodge.py"))     # sections of steps, each with its line in the file
    text = render("dodge", sections)          # the steps as Python, ready to save

An action is ordinary bot code: `with d.step("Wave 1"):` blocks are its sections, and every darbit call in them is
a step. Anything else (a helper call, a calculation) is a Code step kept word for word, so a hand-edited file
survives the editor. A step's note is the comment at the end of its line. See docs/tasks/T14-run-files.md.
"""

import ast
from dataclasses import dataclass, field
from pathlib import Path

KEY_CALLS = {"press", "hold", "release"}
MOUSE_CALLS = {"click", "right_click", "double_click", "hover"}
CHECK_CALLS = {"wait": "wait for", "vanish": "until gone"}


@dataclass
class Step:
    """One step: what kind, the values it needs, and the Python it came from."""

    kind: str  # key, write, wait, mouse, check, if, loop, call, code
    args: dict = field(default_factory=dict)
    note: str = ""
    line: int = 0  # in the file, from 1; 0 for a step not saved yet
    source: str = ""  # the Python, for code steps
    children: list["Step"] = field(default_factory=list)  # inside an `if` or a loop


@dataclass
class Section:
    name: str  # "" for steps outside any `with d.step(...)`
    steps: list[Step] = field(default_factory=list)
    line: int = 0


@dataclass
class Flow:
    name: str
    sections: list[Section]
    calls: list[str] = field(default_factory=list)  # other actions this one calls
    docstring: str = ""
    timed: bool = False  # @d.flow(timed=True): waits keep to the recorded schedule


class FlowError(ValueError):
    """A file that isn't an action; the message says why."""


# ---- reading


def read(path: Path) -> Flow:
    """The action in a file: its sections and steps, with their lines."""
    text = path.read_text(encoding="utf-8")
    try:
        tree = ast.parse(text)
    except SyntaxError as error:
        raise FlowError(f"{path.name}: line {error.lineno}: {error.msg}") from None
    lines = text.splitlines()
    function = _flow_function(tree, path.stem)
    if function is None:
        raise FlowError(f"{path.name}: no @d.flow function")
    imported = _imported_actions(tree)
    sections: list[Section] = []
    loose = Section("")
    for node in _body(function):
        name = _section_name(node)
        if name is not None:
            sections.append(Section(name, _steps(node.body, lines, imported), node.lineno))
        else:
            loose.steps.extend(_steps([node], lines, imported))
    if loose.steps:
        sections.insert(0, loose)
    calls = _calls(sections)
    return Flow(function.name, sections, calls, ast.get_docstring(tree) or "", _is_timed(function))


def _flow_function(tree: ast.Module, stem: str) -> ast.FunctionDef | None:
    named = None
    for node in tree.body:
        if not isinstance(node, ast.FunctionDef):
            continue
        for decorator in node.decorator_list:
            if _decorator_name(decorator) == "d.flow":
                return node
        if node.name == stem:
            named = node
    return named


def _decorator_name(decorator: ast.expr) -> str:
    """`d.flow` for both `@d.flow` and `@d.flow(timed=True)`."""
    if isinstance(decorator, ast.Call):
        return _dotted(decorator.func)
    return _dotted(decorator)


def _is_timed(function: ast.FunctionDef) -> bool:
    for decorator in function.decorator_list:
        if isinstance(decorator, ast.Call) and _dotted(decorator.func) == "d.flow":
            for keyword in decorator.keywords:
                if keyword.arg == "timed" and isinstance(keyword.value, ast.Constant):
                    return keyword.value.value is True
    return False


def _body(function: ast.FunctionDef) -> list[ast.stmt]:
    body = list(function.body)
    if (
        body
        and isinstance(body[0], ast.Expr)
        and isinstance(body[0].value, ast.Constant)
        and isinstance(body[0].value.value, str)
    ):
        body = body[1:]  # its docstring
    return body


def _imported_actions(tree: ast.Module) -> set[str]:
    """Functions imported from sibling action files: `from .dodge import dodge`."""
    found = set()
    for node in tree.body:
        if isinstance(node, ast.ImportFrom) and node.level == 1:
            for alias in node.names:
                found.add(alias.asname or alias.name)
    return found


def _dotted(node: ast.expr) -> str:
    """`d.click` for an attribute chain, `name` for a name, "" otherwise."""
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        base = _dotted(node.value)
        if base:
            return base + "." + node.attr
    return ""


def _section_name(node: ast.stmt) -> str | None:
    """The name in `with d.step("Wave 1"):`, or None for anything else."""
    if not isinstance(node, ast.With) or len(node.items) != 1:
        return None
    call = node.items[0].context_expr
    if isinstance(call, ast.Call) and _dotted(call.func) == "d.step" and call.args:
        first = call.args[0]
        if isinstance(first, ast.Constant) and isinstance(first.value, str):
            return first.value
    return None


def _note(lines: list[str], line: int) -> str:
    """The comment at the end of a line, without the '#'."""
    if not 0 < line <= len(lines):
        return ""
    text = lines[line - 1]
    if "#" not in text:
        return ""
    return text.split("#", 1)[1].strip()


def _constant(node: ast.expr) -> object:
    if isinstance(node, ast.Constant):
        return node.value
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub) and isinstance(node.operand, ast.Constant):
        return -node.operand.value  # a negative number: -12
    raise ValueError("not a constant")


def _spot(node: ast.expr) -> object:
    """A target name, or [x, y] for d.Location(x, y)."""
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    if isinstance(node, ast.Call) and _dotted(node.func) == "d.Location" and len(node.args) == 2:
        return [_constant(node.args[0]), _constant(node.args[1])]
    raise ValueError("not a target")


def _keyword(call: ast.Call, name: str) -> object:
    for keyword in call.keywords:
        if keyword.arg == name:
            return _constant(keyword.value)
    return None


def _steps(nodes: list[ast.stmt], lines: list[str], imported: set[str]) -> list[Step]:
    found = []
    for node in nodes:
        try:
            step = _step(node, lines, imported)
        except ValueError:
            step = None
        if step is None:
            source = "\n".join(lines[node.lineno - 1 : (node.end_lineno or node.lineno)])
            step = Step("code", {}, "", node.lineno, _dedent(source))
        step.line = node.lineno
        if not step.note:
            step.note = _note(lines, node.lineno)
        found.append(step)
    return found


def _dedent(source: str) -> str:
    rows = source.splitlines()
    if not rows:
        return source
    indent = len(rows[0]) - len(rows[0].lstrip())
    trimmed = []
    for row in rows:
        trimmed.append(row[indent:] if row[:indent].strip() == "" else row)
    return "\n".join(trimmed)


def _step(node: ast.stmt, lines: list[str], imported: set[str]) -> Step | None:
    if isinstance(node, ast.Expr) and isinstance(node.value, ast.Call):
        return _call_step(node.value, imported)
    if isinstance(node, ast.If) and not node.orelse:
        test = node.test
        if isinstance(test, ast.Call) and _dotted(test.func) == "d.exists" and test.args:
            timeout = 0
            if len(test.args) > 1:
                timeout = _constant(test.args[1])
            args = {"verb": "if seen", "target": _spot(test.args[0]), "timeout": timeout}
            return Step("if", args, children=_steps(node.body, lines, imported))
    if isinstance(node, ast.While) and isinstance(node.test, ast.UnaryOp) and isinstance(node.test.op, ast.Not):
        inner = node.test.operand
        if isinstance(inner, ast.Call) and _dotted(inner.func) == "d.exists" and inner.args:
            return Step("loop", {"until": _spot(inner.args[0])}, children=_steps(node.body, lines, imported))
    if _is_range_loop(node):
        return Step("loop", {"times": _constant(node.iter.args[0])}, children=_steps(node.body, lines, imported))
    return None


def _is_range_loop(node: ast.stmt) -> bool:
    """`for _ in range(3):`"""
    if not isinstance(node, ast.For) or not isinstance(node.iter, ast.Call):
        return False
    return _dotted(node.iter.func) == "range" and len(node.iter.args) == 1


def _call_step(call: ast.Call, imported: set[str]) -> Step | None:
    name = _dotted(call.func)
    if name.startswith("d."):
        verb = name[2:]
        if verb in KEY_CALLS:
            keys = []
            for argument in call.args:
                keys.append(str(_constant(argument)))
            return Step("key", {"verb": verb, "keys": keys})
        if verb == "write" and call.args:
            return Step("write", {"text": _constant(call.args[0])})
        if verb == "sleep" and call.args:
            return Step("wait", {"seconds": _constant(call.args[0])})
        if verb == "move_by" and len(call.args) >= 2:
            seconds = _keyword(call, "seconds") or 0
            if len(call.args) >= 3:
                seconds = _constant(call.args[2])
            by = [_constant(call.args[0]), _constant(call.args[1])]
            return Step("mouse", {"verb": "move_by", "by": by, "seconds": seconds})
        if verb in MOUSE_CALLS and call.args:
            return Step("mouse", {"verb": verb, "target": _spot(call.args[0])})
        if verb in CHECK_CALLS and call.args:
            return Step(
                "check",
                {"verb": CHECK_CALLS[verb], "target": _spot(call.args[0]), "timeout": _keyword(call, "timeout")},
            )
        return None
    if isinstance(call.func, ast.Name) and not call.args and not call.keywords:
        return Step("call", {"name": call.func.id, "action": call.func.id in imported})
    return None


def _calls(sections: list[Section]) -> list[str]:
    found: list[str] = []
    for section in sections:
        _collect_calls(section.steps, found)
    return found


def _collect_calls(steps: list[Step], found: list[str]) -> None:
    for step in steps:
        if step.kind == "call" and step.args.get("action") and step.args["name"] not in found:
            found.append(step.args["name"])
        _collect_calls(step.children, found)


# ---- writing


def _quote(value: object) -> str:
    return repr(value) if not isinstance(value, str) else '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'


def _spot_text(target: object) -> str:
    if isinstance(target, list) and len(target) == 2:
        return f"d.Location({round(float(target[0]))}, {round(float(target[1]))})"
    return _quote(str(target))


def _number(value: object) -> str:
    number = float(value)  # type: ignore[arg-type]
    if number == int(number):
        return str(int(number))
    return str(round(number, 3))


def statement(step: Step) -> str:
    """One step as its Python statement (the first line, for steps with a body)."""
    args = step.args
    if step.kind == "key":
        keys = []
        for name in args.get("keys", []):
            keys.append(_quote(str(name)))
        return f"d.{args.get('verb', 'press')}({', '.join(keys)})"
    if step.kind == "write":
        return f"d.write({_quote(str(args.get('text', '')))})"
    if step.kind == "wait":
        return f"d.sleep({_number(args.get('seconds', 0))})"
    if step.kind == "mouse" and args.get("verb") == "move_by":
        dx, dy = args.get("by") or [0, 0]
        return f"d.move_by({int(dx)}, {int(dy)}, {_number(args.get('seconds') or 0)})"
    if step.kind == "mouse":
        return f"d.{args.get('verb', 'click')}({_spot_text(args.get('target'))})"
    if step.kind == "check":
        call = "d.vanish" if args.get("verb") == "until gone" else "d.wait"
        timeout = args.get("timeout")
        if timeout is None:
            return f"{call}({_spot_text(args.get('target'))})"
        return f"{call}({_spot_text(args.get('target'))}, timeout={_number(timeout)})"
    if step.kind == "if":
        return f"if d.exists({_spot_text(args.get('target'))}, {_number(args.get('timeout') or 0)}):"
    if step.kind == "loop":
        if "times" in args:
            return f"for _ in range({int(args['times'])}):"
        return f"while not d.exists({_spot_text(args.get('until'))}):"
    if step.kind == "call":
        return f"{args.get('name')}()"
    return step.source


def _lines(steps: list[Step], depth: int) -> list[str]:
    pad = "    " * depth
    found = []
    for step in steps:
        text = statement(step)
        rows = text.splitlines() or ["pass"]
        first = pad + rows[0]
        if step.note and step.kind != "code":
            first += f"  # {step.note}"
        found.append(first)
        for row in rows[1:]:
            found.append(pad + row)
        if step.kind in ("if", "loop"):
            inner = _lines(step.children, depth + 1)
            found.extend(inner or [pad + "    pass"])
    return found


def render(
    name: str, sections: list[Section], docstring: str = "", calls: list[str] | None = None, timed: bool = False
) -> str:
    """The action as a Python file."""
    rows = []
    if docstring:
        rows.append(f'"""{docstring}"""')
        rows.append("")
    rows.append("import darbit as d")
    for other in calls or []:
        rows.append(f"from .{other} import {other}")
    decorator = "@d.flow(timed=True)" if timed else "@d.flow"
    rows += ["", "", decorator, f"def {name}():"]
    body = []
    for section in sections:
        if section.name:
            body.append(f"    with d.step({_quote(section.name)}):")
            body.extend(_lines(section.steps, 2) or ["        pass"])
        else:
            body.extend(_lines(section.steps, 1))
    rows.extend(body or ["    pass"])
    return "\n".join(rows) + "\n"


def from_dict(data: dict) -> Step:
    """A step sent by the Studio (kind, args, note, source, children)."""
    children = []
    for child in data.get("children") or []:
        children.append(from_dict(child))
    return Step(
        str(data.get("kind", "code")),
        dict(data.get("args") or {}),
        str(data.get("note") or ""),
        int(data.get("line") or 0),
        str(data.get("source") or ""),
        children,
    )


def to_dict(step: Step) -> dict:
    children = []
    for child in step.children:
        children.append(to_dict(child))
    return {
        "kind": step.kind,
        "args": step.args,
        "note": step.note,
        "line": step.line,
        "source": step.source,
        "children": children,
    }
