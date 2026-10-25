# 0008 Plain, readable Python

Accepted, 2026-10-25.

## Context

The code was hard to follow for its own owner. There were two causes:

- **Missing explanations:** no overview of how the parts fit together, and modules without a summary.
- **Unfamiliar syntax:** constructs many Python users never meet, such as `:=`, lambdas, conditional comprehensions, `dict.fromkeys` tricks, `getattr` dispatch, `from __future__ import annotations`, and type hints like `tuple[Match | None, bool]`.

## Decision

- **Avoid in bot code** (ad-bot, `examples/`):
  - `:=`;
  - `lambda` (except a one-word sort key);
  - nested or conditional comprehensions and `dict.fromkeys` tricks;
  - `getattr` dispatch;
  - `@staticmethod` without need;
  - chained ternaries;
  - `from __future__ import annotations`;
  - complex type hints.

  In darbit itself, the same constructs are avoided unless they're clearly simpler.
- **Prefer:**
  - plain `for` and `if`, and early `return`;
  - small functions with verb names;
  - small dataclasses for results instead of tuples;
  - named constants with a comment;
  - one idea per line.
- **Explanations:**
  - every module starts with a 2–4 line plain-English summary;
  - docstrings are one line, with arguments only when they're not obvious, and are rendered into the reference docs (mkdocstrings);
  - comments say why, not what;
  - each repo has a code map in `docs/` (for ad-bot: how one run goes through the code).
- **The public API stays SikuliX-simple:** `d.click("Play")`.
- **Enforced** with ruff (lint, format, docstring rules) and pyright in basic mode, through pre-commit and CI.

## Consequences

- ad-bot gets a readable-code pass right after the next bug fix, with behaviour unchanged and tests guarding it. darbit's `runtime/` and `capture/` follow.
- Some code gets a few lines longer; reading it gets faster.
