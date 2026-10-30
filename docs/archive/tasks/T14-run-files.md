# T14 Flows: the file format and model

> **Rewritten 2026-10-26** ([decision 0010](../../decisions/0010-flows-are-python.md)): runs and flows are saved as `@d.flow` Python, not YAML. The first version of this page planned YAML with a JSON Schema.

**Goal:** a recorded run, or a flow made in the Studio, is a Python file that plays by calling it. darbit reads it into a flow model (for the editor and the run panel) and writes it back.

**Depends on:** nothing. **Issue:** #49. **Milestone:** v0.4. **Decisions:** [0007](../../decisions/0007-studio-flows-and-actions.md), [0008](../../decisions/0008-readable-python.md), [0010](../../decisions/0010-flows-are-python.md).

## The file: `runs/slime.py`

```python
"""Slime: clears the Slime dimension, from the lobby to the end screen."""

import darbit as d


@d.flow(window="Roblox")
def slime():
    d.checkpoint("Wave 1", wait_for="Dim.Game.Left", timeout=30)
    d.hold("w")
    d.sleep(0.5)
    d.release("w")
    d.press("q")
    dodge()
    d.turn(-90)  # face the boss door
    d.click(d.spot(0.42, 0.61))
    d.wait("Dim.Game.Next", timeout=60)

    d.checkpoint("Boss", wait_for="Boss.Bar")
    for _ in range(3):
        if d.exists("Boss.Shield"):
            d.press("e")
        else:
            d.press("1")
        d.sleep(1)


def dodge():
    """Jump twice."""
    d.press("space")
    d.sleep(0.3)
    d.press("space")
```

- `slime()` plays it: `True` at the end, `False` when a checkpoint didn't show in time. A bot calls it like any function.
- `d.spot(0.42, 0.61)` is a point as a fraction of the window's content area, so the run plays at any window size. Targets follow their window already (T22).
- The comment on a line is that step's note in the run panel.

## Statements and steps

| Python | Step in the editor |
|---|---|
| `d.press`, `d.hold`, `d.release`, `d.write`, `d.sleep` | key and wait steps |
| `d.click`, `d.double_click`, `d.right_click`, `d.hover`, `d.drag`, `d.scroll` | mouse steps, on a target or a `d.spot` |
| `d.turn(degrees)` | camera turn (written by the recorder, T15) |
| `d.wait(T)`, `d.vanish(T)` | wait for a target to show, or to go |
| `d.checkpoint(name, wait_for=T, timeout=s)` | checkpoint: the run stops with `False` if T doesn't show |
| `if d.exists(T): … else: …` | if / else check (also `if not d.exists(T)`) |
| `while not d.exists(T): …` | until |
| `for _ in range(n): …` | repeat |
| `name()` for a `def` in the same file | call a flow function; its `def` is the function |
| `name()` for an `@d.action` (T29) | an action step |
| anything else | a **Code step**, kept word for word |

## Files

- `packages/darbit/src/darbit/runs/model.py`: dataclasses `Flow` (name, window, steps, doc), `Function`, `Step` (kind, arguments, note, body, otherwise, line); `load(path) -> list[Flow]`, `save(flows) -> str`
- `packages/darbit/src/darbit/runs/flow.py`: `d.flow`, `d.checkpoint`, `d.spot`; `Checkpoint` (the exception a missed checkpoint raises inside a flow)
- `packages/darbit/src/darbit/__init__.py`: export `flow`, `checkpoint`, `spot`
- `packages/darbit/tests/test_flows.py`

## Steps

1. **The calls.** `@d.flow(window=None)` wraps the function: it sets `settings.window` while it runs (if given), records a run-report step per checkpoint, and turns a missed checkpoint into `return False`. `d.checkpoint` waits for its target up to `timeout` (30 s) and raises `Checkpoint` when it doesn't show. `d.spot(x, y)` returns a `Location` from the window's content area now (the whole screen without a window).
2. **Reading** (`load`): `ast.parse`, then every function marked `@d.flow` and every plain `def` it calls, statement by statement, into steps by the table above. A statement that doesn't fit is a Code step holding its exact source text (`ast.get_source_segment`). The note is the comment after the statement on its line. A syntax error is reported with its line.
3. **Writing** (`save`): the module docstring, `import darbit as d`, each flow then its functions, one statement per step, in the plain style (no lambdas, no walrus). Code steps are written back exactly as read.
4. **Round trip:** `save(load(text)) == text` for any file `save` wrote, and for hand-written files that only use flow statements and are formatted by `ruff format`.
5. **Checks** on load: a flow function calling itself (directly or through others) is an error naming both; a `d.checkpoint` without `wait_for` is an error.

## Contracts

- The file shape above and the statement table: the recorder (T15), the player and run panel (T16), the editor (T27) and actions (T29) all rely on it.
- `d.flow`, `d.checkpoint`, `d.spot`, and a flow returning `True`/`False`.
- `Step.kind` names: `press`, `hold`, `release`, `write`, `sleep`, `click`, `double_click`, `right_click`, `hover`, `drag`, `scroll`, `turn`, `wait`, `vanish`, `checkpoint`, `if`, `until`, `repeat`, `call`, `code`.

## Done when

The example above loads into the model, saves back to the same text, plays against a fake screen (checkpoints seen and missed), and a hand-edited version with an extra Python line keeps that line as a Code step.

## Tests

Round trip for every step kind; Code steps kept exactly; notes; nested `if`/`for`/`while`; a missed checkpoint returns `False`; recursion and missing `wait_for` errors; `d.spot` with and without a window (faked).

## Not in this task

`d.turn` and recording (T15), the player's pause and step (T16), the editor (T27), keeping comments between statements and odd formatting through an edit (T28).
