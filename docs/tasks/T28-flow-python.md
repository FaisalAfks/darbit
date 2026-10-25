# T28 Flow ↔ Python

**Goal:** a flow can become readable Python, and flow-shaped Python can be opened as a flow, so the same bot is edited in the Studio and in a code editor.

**Depends on:** T14, T27. **Milestone:** v0.5. **Decision:** [ADR 0007](../decisions/0007-studio-flows-and-actions.md).

## How

- **Flow → Python:** one statement per step, in the plain style of [ADR 0008](../decisions/0008-readable-python.md). Functions become `def`s; checks become `if d.exists(...)` and `d.wait(...)`; loops become `for` and `while`. The file starts with `@d.flow`.
- **Python → flow:** the Studio parses the file with Python's own `ast` module, so no decompiler is needed. Inside a `@d.flow` function:

  | Python | Flow step |
  |---|---|
  | `d.press`, `d.hold`, `d.click`, `d.wait`, `d.sleep` | the matching steps |
  | `if d.exists(T): … else: …` | an if/else check |
  | `while not d.exists(T)` | `until` |
  | `for _ in range(n)` | `repeat` |
  | a call to a `def` in the same file | a function call |
  | a call to an `@d.action` | an action step |
  | anything else | a **Code step**, kept word for word |

- **Round trip:** saving Python → flow → Python gives the same text for anything that was flow-shaped.

## Files

- `src/darbit/runs/export.py`: flow → Python
- `src/darbit/runs/parse.py`: Python → flow (with `ast`)
- `tests/test_flow_python.py`: round-trip cases

## Done when

A flow with checks, a loop and a function exports to Python, opens in VS Code, is edited there (a wait changed, a step added), and opens again in the Studio with the edits in place.
