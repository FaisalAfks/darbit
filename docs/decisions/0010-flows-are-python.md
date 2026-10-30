# 0010 Run files and flows are saved as Python

Accepted, 2026-10-26. Replaces the YAML run files of [design.md §8](../archive/design.md) and the first T14 page.

## Context

T14 planned recorded runs as YAML with a JSON Schema, played by an interpreter. [0007](0007-studio-flows-and-actions.md) then made recordings flows and said flows are saved as flow-shaped Python that the Studio reads back with `ast`. Two formats for one thing would mean two loaders, an export step between them, and runs that VS Code can only edit as data.

## Decision

A run or flow is a Python file: a function marked `@d.flow`, written only with flow statements (darbit calls, `if d.exists(...)`, `for _ in range(n)`, `while not d.exists(...)`, calls to other functions in the file). Anything else in it is a Code step, kept word for word.

- **Playing** a flow is calling the function. No interpreter: the recorder writes Python, and Python runs it.
- **The Studio** reads the file with `ast` into a flow model for the editor and the run panel, and writes it back the same way.
- **New calls** for what runs need: `d.flow` (the decorator), `d.checkpoint(name, wait_for, timeout)` (the run must see this before going on), `d.spot(x, y)` (a point as a fraction of the window), `d.turn(degrees)` (the camera).
- A flow returns `True` when it reached the end, `False` when a checkpoint didn't show.
- A step's note is the comment on its line. Breakpoints are kept by the Studio in the project's `.darbit/`, not in the file.

## Consequences

- No `pyyaml`, no JSON Schema. Editors already know Python; the step palette and help come from the darbit API.
- T14 becomes the flow model, the file shape, `load`/`save` with `ast`, and `d.flow`, `d.checkpoint`, `d.spot`. T15 adds `d.turn` and its calibration, and writes `runs/<name>.py`. T16 plays and steps through a flow. T28 is left with keeping a hand-edited file intact through the editor.
- A recording is ordinary bot code from the first second, so growing it into a bot is editing, not converting.
