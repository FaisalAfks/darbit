---
name: new-task
description: Start work on a task from docs/tasks (or a new one) with its issue, branch, placeholders, tests and PR.
---

# Start a task

1. Read the task page in `docs/tasks/` (or write one with the same headings: Goal, Depends on, Files, Steps, Contracts, Done when, Tests, Not in this task) and the decisions it links.
2. Check its "Depends on" tasks are merged. If not, stop and say so.
3. Find or open its issue; it should be on the project board in the task's milestone.
4. Branch from the latest `main`: `feature/<issue>-<short-name>` (or `fix/…`).
5. Fill in the placeholder files the page names (`TODO(Txx)`). Follow `docs/style/code.md`: plain Python, a module summary, short docstrings.
6. Tests first where the code is pure (no screen, mouse or keys); fakes and saved screenshots otherwise. `uv run pytest`, `uv run ruff check .`.
7. Update `CHANGELOG.md` (Unreleased) and the docs the change touches; add a decision record if the change sets a new rule.
8. Open the PR: what changed, why, `Closes #<issue>`, in the owner's voice. Ask the owner before merging.
