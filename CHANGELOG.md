# Changelog

## Unreleased

### Docs

- darbit Studio's redesign (decision 0013): structure, look, every page, Capture and the Recorder, chosen from rendered options in `docs/ui/redesign/`

### New

- darbit Studio, first usable version: `darbit app` (needs `darbit[app]`) opens it in a desktop window. Pick a bot (installed, or any project folder you add), run, pause and stop it, and see its Overview, pictures with their last scores, past days and settings; the dock opens Capture, Guide and Check for it
- darbit Studio's new frame (decision 0013): a bot dropdown or sidebar, a centred page bar (Overview, Results, Library, Settings) with a gliding highlight, Play, Pause, Stop and Edit, page fades, and the Studio's own settings page (look, window, while a bot runs)
- Actions: recorded or written steps saved as an `@d.flow` function in the bot's `actions/` folder (decision 0010), and `d.flow` to mark one
- The recorder (Library › Actions › Record, with Edit on): the Studio hides and a bar at the top records every key and click; Ctrl+Alt+P pauses, and while paused a wait or a picture check is added at that moment; the live steps panel shows what's caught and the last step can be dropped; Ctrl+Alt+R stops and opens the action. darbit's own hotkeys and clicks on the bar aren't recorded
- The action editor: one list with sticky, foldable sections, Jump to and search; steps as keycaps, picture thumbnails and wait bars; settings that unfold under a step; insert between rows, drag to reorder, pick many to delete or speed up waits; calls to other actions with Peek and Open; and Play, which runs the action and follows it line by line with breakpoints, Step and Stop
- Capture rebuilt in the Studio's look (decision 0013): it opens over the frozen game from the Studio (Start setup, Retake, Capture), hides the Studio first, and saves into the open bot. A click boxes what's there (again for bigger, right-click for smaller); the box can be dragged, resized from 8 handles, scaled with the wheel and nudged with the arrows; Shift+drag sets where to search and Ctrl+click the click point. A magnifier follows the mouse. Test finds the boxed picture in its region and marks every match with its score, look-alikes included, against a similarity slider. With a setup guide, a small bar names the next picture between screens, and Ctrl+Alt+C freezes again
- Global hotkeys from the keymap's [global] scope (RegisterHotKey)
- The bot's Settings page: sections on the left with search, one form on the right, a dot on every value changed from its default with a way back to it, and a save bar that slides up while there are unsaved changes
- The Library page: every asset (images, regions, points, and the guide's pictures still missing) grouped by screen, with filters, search, a score meter against the similarity each needs, and how often each is used; the inspector shows an asset's numbers, its last checks and every line that uses it, and with Edit on, Retake and Rename, which previews each changed line and then renames the files and every line together or not at all
- The Overview page in blocks of rows: Now, what needs you (a failure with Retake, pictures still to take with Start setup), today's round with the steps still to come (`d.plan`), progress, today's gains, next up, what happened and what's watched; Customize rearranges, resizes and hides blocks, saved per bot on this PC
- The Results page: a day list with each day's lead gain, and the chosen day as a sentence, its problems grouped with a Retake, a table of gains (today, the week, total) and progress, and a whole-day timeline that zooms and drags
- `d.record.gain(name, amount, total=, icon=)` reports what the bot got, and `d.plan([...])` the round's order; `d.record(...)` works as before
- Closing the Studio keeps darbit running in the tray: the icon gets a dot while a bot runs, and its menu pauses, stops or shows the running bot, opens the Studio settings or quits; the window opens where it was left
- The run pill: pressing Run shrinks the Studio to a bar at the top of the screen with the bot's current step, Pause, Stop and a way back. It slides away after 3 s; moving the mouse to the top edge brings it back, but the bot's own mouse moves never do. It can be turned off in the Studio's settings
- Bots started from the Studio can be paused and stopped without ending the process: darbit watches a control folder given in `DARBIT_CONTROL`

## 0.3.0 - 2026-10-26

Bots become projects with their own settings, darbit gets one command for everything, and darbit Studio gets its foundations: the local server, the UI package and its components, and what a bot shows in it.

### New

- Bot projects: a `darbit.toml` next to the bot (or above its script) gives its name, version and the darbit it needs, and sets darbit's settings for it before the script runs; image folders from `[images]` are searched first. A darbit version that doesn't match is a warning. Without one nothing changes
- A bot's own settings: `settings.toml` declares them (sections, types, limits, help), `config.toml` is checked against it and made from the defaults when missing, and saving keeps its comments
- The `darbit` command: `darbit new NAME` makes a bot project, `darbit install GIT_URL` clones one at its newest release with its own uv environment, `darbit run` starts it; `darbit capture`, `guide`, `check` and `report` run the tools
- Setup guides: `guide.toml` lists the screens to open and the targets to take on each, in order; `darbit guide` walks through it, and `--guide capture.txt` converts a list once
- Targets follow their window: taken with `--window`, a target's region, point and picture move and resize with the window; a target taken at another display scaling is resized; a resized target not found is tried at nearby sizes, at most once a minute
- What a bot shows in darbit Studio (decision 0011): `d.progress(label, done, total)` and `d.next(label, at)`, an optional `[studio]` table, and the Overview's tiles built from the run report; observers record when they start, fire and stop
- The local server for darbit's windows (`darbit[app]`): one WebSocket per window with a token, requests and events, screens as raw pixels (a 2560 x 1600 screen in about 65 ms), the keymap, theme and UI settings; log lines and run-report events reach every open window
- The web UI package: built into the wheel; four themes (glass-dark, glass-light, midnight, high-contrast); components for every window in Storybook (`npm run storybook`)

### Changed

- The UI follows Fluent 2's scales and WCAG 2.2 AA (decision 0012); `npm run check` fails on a missing token, a colour or raw pixel size outside the tokens, or a colour pair below the contrast line
- darbit's own code follows the plain style of decision 0008 (no walrus, lambdas, `@staticmethod` or `__future__` imports), checked in pre-commit and CI
- Runs and flows are saved as `@d.flow` Python (decision 0010); `examples/hello-bot` and `darbit new` use the agreed layout (`src/<name>/`, `assets/images/`)
- The docs site is published on GitHub Pages; releases upload only the wheel and the source package; Dependabot groups its updates weekly

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
