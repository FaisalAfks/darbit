# 0007 The hub becomes darbit Studio: flows, actions, two-way with Python

Accepted, 2026-10-25.

## Context

Bots are written in Python. The recorder (T15) was planned to save runs as YAML for a player. The goal now is wider: build bots in the app without code, prototype fast with a recorded macro, then grow it with image checks and logic, without ever locking out code.

## Decision

The hub is renamed **darbit Studio**, and recordings are **flows**.

1. **Record with checks.** While recording, pause and use **Add check**:
   - an image check opens the capture tool, saves the picture into the bot's `assets/images/`, and inserts a check at that point: wait for it, if seen, if not seen, until gone;
   - other checks: a colour at a point, a region changing, and text later.

   Then resume.
2. **Flows** are edited as a list or a graph: input steps, checks (`wait_for`, `if`/`else`, `until`, `retry`, `on_fail`), `repeat`, `set`, and calls.
3. **Actions** are one idea in the editor. Each has parameters and an optional result, and all are called the same way. There are three kinds:
   - built-in steps;
   - **functions** defined in a flow: a named sub-flow with inputs and a result, shareable between flows and bots;
   - **Python actions**: functions marked `@d.action`, whose typed parameters become a form in the step palette.
4. **Code steps** call any bot function, or hold a short script, for whatever the editor can't express.
5. **Two-way with Python, without a decompiler:**
   - **Flow → Python:** writes readable darbit code, one statement per step; flow functions become `def`s.
   - **Python → flow:** flows are saved as flow-shaped Python, a `@d.flow` function using only flow statements (`d.wait`, `if d.exists(...)`, loops, calls, `d.press`). The Studio reads it back with Python's own `ast` parser. Anything outside that shape becomes a Code step, kept word for word.

## Consequences

- One flow model and schema serves the recorder, the player, the editor and export. T14 is redefined to include functions (`define`, `call`, `return`) from the start.
- New tasks:
  - T26 checks while recording;
  - T27 flow editor;
  - T28 flow ↔ Python;
  - T29 custom steps with `@d.action`.
- Roadmap: v0.4 is "runs and flows"; the editor and round trip ship with the Studio in v0.5.
- These screens are designed first, in the last HTML concept round (ADR 0005).
- The Studio and the library ship from one package (`darbit[app]`), so a standalone Studio installer later is packaging work, not a rewrite.
