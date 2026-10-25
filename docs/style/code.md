# Code style

Plain, readable Python that anyone who knows the basics can follow ([decision 0008](../decisions/0008-readable-python.md)). Checked by ruff in CI.

## Write

- Plain `for` and `if`; early `return` instead of deep nesting.
- Small functions with verb names (`find_card`, `save_marked_screenshot`), one job each.
- A small `@dataclass` for a result with more than one value, instead of a tuple (`Card(match, used)`).
- Named constants with a comment saying what the number means (`USED_BRIGHTNESS = 0.65  # darker than this share is greyed out`).
- One idea per line; split long conditions into named booleans (`moved = …`, `already_there = …`).
- Type hints on every function, kept simple (`Match | None`, `list[str]`).

## Avoid

| Instead of | Write |
|---|---|
| `if (m := d.exists(x)):` | `m = d.exists(x)` then `if m:` |
| `lambda: …` | a named `def` (a one-word sort key is fine: `key=len`) |
| `[x for x in xs if cond]`, nested comprehensions | a loop that appends |
| `dict.fromkeys(...)` to drop duplicates | a loop with `if item not in seen` |
| `getattr(obj, name)(…)` | `if`/`elif` on the name |
| `@staticmethod` | a module function, or a plain method |
| `a if c else b` inside expressions | `if`/`else` statements |
| `from __future__ import annotations` | nothing (Python 3.11+ doesn't need it) |
| `tuple[Match \| None, bool]` | a small dataclass |

In darbit's own internals a comprehension or a ternary is fine when it's clearly the simplest form. Bot code (and `examples/`) avoids them always.

## Explain

- **Every module** starts with a 2–4 line plain-English summary: what it's for, and how its parts fit.
- **Docstrings** are one line saying what a function does or returns; arguments only when they aren't obvious. The reference docs are built from them (mkdocstrings).
- **Comments** say *why*, not *what*.
- **Bigger pictures** go in `docs/`: [architecture](../architecture/index.md), guides, decisions.

## Structure

- Layers only import downward ([architecture](../architecture/index.md)).
- The public API is what `darbit/__init__.py` exports. Keep it SikuliX-simple.
- Not found → `None`/`False`; exceptions are for mistakes (a missing file, a bad argument) and for stopping.
- Studio-only packages (`starlette`, `uvicorn`, `pywebview`) are imported inside functions.

## Tools

```bash
uv run ruff check .     # lint
uv run ruff format .    # format
uv run pytest           # tests: fakes and saved screenshots, never live input
```
