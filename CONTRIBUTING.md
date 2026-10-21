# Contributing to darbit

darbit is a simple GUI-automation toolkit for Windows, in Python: an improvement on SikuliX, not a framework. Read [docs/design.md](docs/design.md) once, then pick a task from [docs/tasks](docs/tasks/README.md).

## Picking up a task

1. Each task has its own page in `docs/tasks/` and an issue on the board. The page is the instructions; the issue tracks it.
2. Check the task's **Depends on** line. Don't start a task whose dependencies aren't merged.
3. The placeholder files a task names already exist with their signatures and a `TODO(Txx)` note. Fill them in; don't move them without a reason written in the PR.
4. A task is done when everything under **Done when** is true and shown (tests, a screenshot or a short clip for UI).

## Rules

- **Branches and PRs.** Never commit to `main`. One branch per task: `feature/<issue>-<short-name>` or `fix/<issue>-<short-name>`. Open a PR into `main` that says `Closes #<issue>`. The owner merges.
- **Small PRs.** One task per PR. If a task grows, split it and say so on the issue.
- **Writing.** Commits, PRs, docs and comments are plain and short, and describe what changed and why it matters to the code. No "I" or "we", no notes about how the work was done.
- **Simple first.** The public API stays as simple as SikuliX: `d.click("Play")`. Not finding something is `None` or `False`, never an exception.
- **Layers.** `core` (pure, no screen) ← `platform` (Windows) ← `runtime` ← `tools` / `capture` / `runs` / `project` ← `server` ← `desktop`. A layer only imports from layers below it.
- **Optional parts stay optional.** The web UI, the server and the desktop windows need the `ui` extra (`pip install -e ".[ui]"`). `import darbit` must keep working without it: import those packages inside functions.
- **No live input in tests.** Tests never move the mouse or press keys. Use fakes and saved screenshots (`tests/`); live checks are done by hand and described in the PR.
- **Speed.** Anything that runs per frame or per tick gets a number in the PR (ms per call, before and after).
- **Line endings.** Keep each file's existing line endings; don't rewrite whole files to change a few lines.

## Setting up

```bash
pip install -e ".[dev,ui]"
cd ui && npm install && npm run dev
```

- `ruff check .` and `pytest` must pass (CI runs both on Windows).
- `npm run build` in `ui/` writes the web UI into `src/darbit/ui/static/`, which is shipped in the wheel.

## Where things go

| Path | What |
|---|---|
| `src/darbit/core` | geometry, targets, matching, run-file model |
| `src/darbit/platform` | screen capture, input, windows, hotkeys and hooks |
| `src/darbit/runtime` | find, act, wait, observers, state, logs, highlight |
| `src/darbit/capture` | the capture tool: `engine/` (pure selection and snapping), `guide.py`, the session |
| `src/darbit/runs` | run files: model, recorder, player |
| `src/darbit/project` | `darbit.toml`, settings schema |
| `src/darbit/server` | the local server and its messages |
| `src/darbit/desktop` | desktop windows (pywebview) |
| `src/darbit/keymap.py`, `keymap.toml` | every shortcut in the suite |
| `ui/` | the web UI: tokens, themes, components, and one app per window |
| `docs/tasks/` | instructions per task |
