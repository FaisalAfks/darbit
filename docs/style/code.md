# Code style

Idiomatic, readable Python ([decision 0015](../decisions/0015-rebuild.md), which relaxes [0008](../decisions/0008-readable-python.md)). Checked by ruff, and by pyright for the core.

## Write

- Small functions with verb names (`find_card`, `save_marked_screenshot`), one job each.
- Early `return` instead of deep nesting; one idea per line; long conditions split into named booleans.
- A small `@dataclass` for a result with more than one value, instead of a tuple.
- Named constants with a comment saying what the number means (`USED_BRIGHTNESS = 0.65  # darker than this is greyed out`).
- Type hints on every function.
- Simple comprehensions are fine (`[asset.name for asset in assets]`), and so is a lambda as a sort key.

## Avoid

- Clever one-liners: nested comprehensions, comprehensions with side effects, chained ternaries.
- The walrus operator (`:=`), `getattr` dispatch, `from __future__ import annotations` (Python 3.11+ doesn't need it).
- Stub files for future work: future work is an issue, not a `TODO` module.

Bot code and `examples/` stay the plainest: loops over comprehensions, no lambdas.

## Explain

- **Every module** starts with a 2–4 line plain-English summary: what it's for, and how its parts fit.
- **Docstrings** are one line saying what a function does or returns; arguments only when they aren't obvious. The reference docs are built from them.
- **Comments** say *why*, not *what*.
- **Bigger pictures** go in `docs/`: the [rebuild plan](../plan-rebuild.md), [architecture](../architecture/index.md), guides, decisions.

## Structure

- The public API is what `darbit/__init__.py` exports. Keep it SikuliX-simple.
- Not found → `None`/`False`; exceptions are for mistakes (a missing file, a bad argument) and for stopping.
- System-specific code sits behind the interfaces in the rebuild plan (screen, input, windows, listener, hotkeys), never spread through other modules.
- Studio-only packages are imported inside functions, so `import darbit` works without them.

## Tools

```bash
uv run ruff check .     # lint
uv run ruff format .    # format
uv run pytest           # tests: fakes and saved screenshots, never live input
```
