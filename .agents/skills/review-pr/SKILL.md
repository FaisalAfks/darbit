---
name: review-pr
description: Review a darbit PR against the repo's rules before asking the owner to merge.
---

# Review a PR

Check, in this order:

1. **CI is green.** `uv run pytest` and `uv run ruff check .` pass locally too.
2. **One task:** the PR closes its issue and does only that task; nothing unrelated slipped in.
3. **Behaviour:**
   - edge cases are handled;
   - not-found returns `None`/`False` instead of raising;
   - nothing blocks the stop hotkey;
   - nothing touches the real mouse or keys in tests.
4. **Readable Python** (`docs/style/code.md`):
   - none of the banned constructs;
   - a module summary;
   - short docstrings;
   - names that say what things are.
5. **Layers:** imports only go downward; Studio-only packages are imported inside functions.
6. **Docs:** the changelog line is there; docs and task pages match the change; a decision record exists if the change sets a rule.
7. **Writing:** the PR, commits and comments follow `docs/style/writing.md`.
8. **Line endings:** no whole-file rewrites from line-ending changes (`git diff --ignore-cr-at-eol --stat` shows the real size).

Report findings as a short list, most important first, with file and line.
