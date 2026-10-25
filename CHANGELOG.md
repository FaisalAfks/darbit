# Changelog

## Unreleased

## 0.2.0 - 2026-10-25

The runtime grows up (observers, saved state, run reports, library checks), the capture tool gets a real engine, and the repo is set up for darbit Studio.

### New

- Observers: `d.observe(image or condition)` watches in the background; the next darbit call raises `Interrupted` and held keys are let go; `d.no_interrupts()` for quiet blocks
- `d.State(name)`: saved values, counters, daily and weekly resets, timers
- Run report: `report-<day>.jsonl` with searches (closest score when not found), clicks, `d.step(name)` and `d.record(event)`; `python -m darbit.tools.report` summarises a day
- `python -m darbit.tools.check`: every target scored in its region and everywhere else, against the live screen or saved screenshots, with a verdict and a history
- A search that finds nothing logs its closest score and spot
- Waiting for several targets takes one screen capture per look, covering all their regions
- Capture engine: click to select at any size (click again for bigger, right-click for smaller), up to whole windows; edges snap exactly onto borders; regions and points show their position and size; the magnifier draws the boxes; Shift+drag draws a region, Ctrl+click sets the click point
- `darbit.paths`: the folders darbit uses (user settings in `%APPDATA%\darbit`, app data and cache in `%LOCALAPPDATA%\darbit`, a project's `.darbit`)
- The `darbit` command (more subcommands come with the Studio)
- Docs site (`uv run --group docs mkdocs serve`), `AGENTS.md`, `.agents/skills`, decision records, task pages, the Studio mockups and `examples/hello-bot`

### Changed

- A script's logs and saved state go in its `.darbit/` folder (`.darbit/logs`, `.darbit/state`) instead of `logs/` and `state/`; set `settings.logs` / `settings.state` to keep the old places
- Screenshots are saved as JPEG (quality 85), about 10 times smaller; the newest 200 are kept, old PNGs included
- The repo is a monorepo: the package is in `packages/darbit`; install from git with `#subdirectory=packages/darbit`
- The optional extra `ui` is now `app`
- Development uses uv (`uv.lock`, Python 3.13), ruff format, pre-commit, Dependabot and a release workflow

### Removed

- Capture tool: the grid harvest (`--harvest`) and `--from script.py`

## 0.1.0 - 2026-10-21

First version: what a SikuliX script needs, in Python.

- Targets: images, locations, or both, loaded by name from the image folders, with an optional `.json` for region, similarity and click offset
- Finding and waiting: `exists`, `wait` (one or several targets), `vanish`, `find_all`, `check`; not found is `None` or `False`
- Mouse: `click`, `double_click`, `right_click`, `hover`, `drag`, `scroll`, with a gliding mouse
- Keyboard: `press`, `hold`, `release`, `write`; keys by position, any keyboard language
- Apps: `apps.open`, `apps.close`, `apps.running`, `apps.focus`, `apps.window`
- Settings, stop hotkey (Ctrl+Alt+Q), `sleep`, keeping the PC awake, releasing keys on exit, an optional window that must be in front
- Real screen pixels on scaled displays
- Log file per day and a screenshot when a long wait runs out
- Capture tool: single targets, guided sessions from a list file with a hiding card, one shot per screen, click to box, snapping, live check, undo and cleanup, and harvesting scrolling lists
