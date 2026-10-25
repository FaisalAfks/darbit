# T20 Hub app

> **Renamed 2026-10-25** ([ADR 0007](../decisions/0007-studio-flows-and-actions.md)): the hub is **darbit Studio**. It also installs bots through a wizard, launches every tool for the selected bot, and hosts the flow editor (T27).

**Goal:** the desktop home of darbit: your bots, their settings, start and stop, what they're doing now, their history and their image library, with every tool one click away.

**Depends on:** T03, T05, T11, T18, T19. **Issue:** #53. **Milestone:** v0.5.

## Layout

A `normal` window, 960 × 640 (down to 720 × 480). A slim rail on the left with five sections; `ctrl+tab` cycles them.

| Section | Shows |
|---|---|
| **Bots** | a card per installed project: name, accent, status dot (idle, running, paused, failed), last run; Run/Stop on the card; `+` installs from a git link or makes a new one |
| **Bot** (the open one) | a header with Run/Pause/Stop and the current step; tabs: **Live** (the step timeline as it runs, the log tail, the last screenshot), **Settings** (T18 form), **Setup** (guide progress, T12) |
| **Library** | every target as a thumbnail with its last score (`ScoreBadge`), kind, region link; filter by screen or verdict; select → Highlight (T11), Retake (T09), Rename, Delete |
| **Runs** | history from the run reports: days, steps with ok/failed counts and times, failures with their screenshots (today's `darbit report`, as a page) |
| **Settings** | theme, keymap editor (T04 KeyEditor), folders, start with Windows |

## Compact mode

`ctrl+.` turns the hub into a 300 × 48 pill (a `bar` window, on top, no focus): bot name, status, current step in one line, Run/Pause/Stop. Again to restore.

## Files

- `packages/ui/src/apps/hub/App.svelte`, `Rail.svelte`, `Bots.svelte`, `Bot.svelte`, `Library.svelte`, `Runs.svelte`, `Settings.svelte`
- `packages/darbit/src/darbit/server/hub.py`: handlers `projects.list`, `project.run`, `project.stop`, `project.pause`, `library.list`, `reports.days`, `reports.day`
- `packages/darbit/src/darbit/desktop/__main__.py`: `darbit app` opens it

## Steps

1. Running a bot from the hub starts it as a child process (its venv) with `DARBIT_SERVER` set, so its darbit publishes to the hub's server; stdout goes to the Live log.
2. Pause and stop go through the bot's darbit (the server sends `run.pause`/`run.stop` to the child, which acts like the global hotkeys).
3. The Live step timeline is built from `step` events (v0.2 run report): nested steps, durations, failures with screenshots.
4. Library thumbnails are made once by the server (96 px WebP, cached by file time) and lazy-loaded.
5. Everything updates by events; no polling.
6. Budget: the hub idles at < 1% CPU and < 150 MB with a bot running. Numbers in the PR.

## Done when

ad-bot is installed, set up, run, paused, stopped and its last day reviewed, all from the hub; compact mode works over the game.

## Tests

Server handlers with a fake project folder; the UI by hand with screenshots of each section in two themes.
