# Changelog

## Unreleased

### New

- darbit's new logo (`assets/logo.svg`): a "d" whose bowl is a target ring with the match at its centre, on a dark glass tile in the cyan-to-violet accent. It's darbit Studio's icon on its windows, the taskbar, Alt+Tab and the tray, where Python's icon showed before

## 0.4.0 - 2026-10-29

### Changed

- Smoother Studio, Capture and recorder: real input now comes through Raw Input instead of low-level hooks, so a busy darbit can never make the mouse or the game's keys lag; blur only on the small top bars; glowing and pulsing effects animate opacity and transform instead of repainting shadows; the background is its own fixed layer; Capture dims the shot with four panels and reads the magnifier's colour from a CPU copy of the shot

### Fixed

- `darbit app` failed to start (`'list' object is not callable` while reading the screens)
- Only the page scrolls now; the top bar stays put
- Dragging on Capture moved the whole overlay instead of drawing a box, and Esc and the other keys didn't reach it
- A second `darbit app` while the Studio is in the tray brings it back instead of opening another Studio and tray icon
- The Library opens faster: it skips the bot's environment and git folders, counts uses in one pass and keeps thumbnails until the file changes
- The first hour on the Results timeline was cut off
- The Library showed old pictures after a retake until the bot was opened again: a saved picture now redraws its card at once, coming back to the Library shows the last list straight away while it checks for changes, and only changed thumbnails are sent
- Retake from the Overview or Results opened Capture with an empty name: it now fills in the picture the failure names
- Stop from the Studio didn't stop a bot whose own darbit is older than the Studio's stop (v0.3.0 and before), and ending it then left the bot running: `uv run` starts the bot as a child that outlives its parent. The Studio now ends the whole process tree (at once for a bot that can't see its stop), then lets go of every key and button. A bot started by an earlier Studio is still known through its pid, so it can be stopped and isn't started twice
- The Studio kept a CPU core busy while a bot ran: every second it read and parsed the whole day's report (a few MB) and rebuilt the Overview, twice. The report is now read a bit at a time (only new lines, about 10 ms instead of 100), the Overview is made again only when the report, the minute, the guide or the pictures change, the Studio looks every 2 s, and a hidden Studio doesn't redraw at all until it's shown
- Pausing a recording kept held keys down for the rest of the tape and kept the paused time in it: pausing now lets go of held keys on the tape and leaves the pause out
- Recording with the name of an existing action replaced it without asking: it now has to be Re-record
- After the stop hotkey (Ctrl+Alt+Q) ended one played action, every later Play in the same Studio ended at once without doing anything: each Play now starts fresh, so Ctrl+Alt+Q is the way to stop a played action
- The recorder bar, the run pill and Capture's next-picture bar showed a grey box around them and the recorder's buttons could be cut off: bars now fill their own window, with rounded corners, and long text ends in …
- The checkpoint key moves to Ctrl+Alt+K (Ctrl+Alt+M is often taken by other programs), and the recorder bar warns when another program has one of its keys
- The recorder lost mouse counts and bunched events whenever darbit Studio was busy (38 of 200 counts caught in a test): Python only switched threads every 5 ms. While recording or playing a tape, threads now switch every 0.5 ms, and every count arrives on time
- Playing an action from the Studio clicked on the Studio itself: it now hides while the action plays and comes back at a breakpoint or the end
- The recorder takes each click's place from when it happened, not when it was handled
- Keys held by an action were left down when it stopped or failed: Play lets go of every key and button at the end
- A recorded Shift+E played back as Shift, then E: combos are now one press (`d.press("shift+e")`)
- A recorded drag (turning Roblox's camera with the right button) played back as the movement and then a click, so the mouse ran off to the edge: it's now `d.mouse_down`, the movement, then `d.mouse_up`

### Docs

- darbit Studio's redesign (decision 0013): structure, look, every page, Capture and the Recorder, chosen from rendered options in `docs/ui/redesign/`

### New

- Recorded actions keep their timing: the recorder writes `@d.flow(timed=True)` and waits to 0.01 s, and in a timed action each wait ends on the recorded schedule, with the time the steps took taken out of it; clicks glide 0.03 s instead of 0.5 s
- Recordings are tapes (decision 0014): every mouse packet, key, button and wheel notch with its time, played on one clock by `d.replay(__file__, start, end)`. While a game holds the cursor (Roblox's shift lock, a right-drag) the same counts are sent, so the camera turns the same; otherwise the cursor goes exactly where it went, whatever Windows' mouse settings. Places follow the game window. Checks added while recording split the tape into parts, and the editor shows each part with a mini path and marks, to trim or split
- `d.move_by`, `d.mouse_down`, `d.mouse_up` and a sideways wheel for hand-written actions
- Checkpoints while recording (Ctrl+Alt+K, or ⚑ on the bar): each part becomes its own action with its own tape (Dim_Run_1, Dim_Run_2…), and the recorded action plays them in order. Re-record (with Edit on) replaces one action, so a single part can be done again without touching the rest; Rename renames an action, its tape and every action that calls it
- A second `darbit app` brings the Studio in front of the game, not just out of the tray
- Delete (with Edit on) removes an action, its tape and its breakpoints; an action another one still plays says which and stays
- Delete for assets in the Library (with Edit on): it removes the picture and its settings, and says how many lines still use it
- darbit Studio, first usable version: `darbit app` (needs `darbit[app]`) opens it in a desktop window. Pick a bot (installed, or any project folder you add), run, pause and stop it, and see its Overview, pictures with their last scores, past days and settings; the dock opens Capture, Guide and Check for it
- darbit Studio's new frame (decision 0013): a bot dropdown or sidebar, a centred page bar (Overview, Results, Library, Settings) with a gliding highlight, Play, Pause, Stop and Edit, page fades, and the Studio's own settings page (look, window, while a bot runs)
- The Library's Screen view: each screen's last shot from Capture with its assets drawn in place; the inspector shows the chosen asset glowing on its screen, and Test on screen opens Capture straight into Test for it, searching its own region
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
