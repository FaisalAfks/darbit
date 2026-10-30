---
name: new-task
description: Start work on an issue from the rebuild plan's milestones, with its branch, tests and PR.
---

# Start a task

1. Read the issue and the part of `docs/plan-rebuild.md` it belongs to (its milestone and done-test).
2. Check the work it depends on is merged. If not, stop and say so.
3. Branch from the latest `main`: `feature/<issue>-<short-name>` (or `fix/…`).
4. Follow `docs/style/code.md`: a module summary, short docstrings, system-specific code behind the plan's interfaces, every detection change an option (the default stays as it is).
5. Tests first where the code is pure (no screen, mouse or keys); fakes and saved screenshots otherwise. `uv run pytest`, `uv run ruff check .`.
6. Update `CHANGELOG.md` (Unreleased) and the docs the change touches; add a decision record only for a real fork in the road.
7. Open the PR: what changed, why, `Closes #<issue>`, in the owner's voice. Merge once its checks pass.
