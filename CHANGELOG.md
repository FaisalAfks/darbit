# Changelog

## Unreleased

### New

- Capture makes a target's picture, its area and its click point together (round 11, A): drag or click for the picture, Shift+drag for its area, Ctrl+click for the point. The pill moved to the top, shows the three parts, and slides away until the mouse comes to the top edge, so what was under it can be boxed. Ctrl+Z and Ctrl+Y undo and redo every change; readouts take exact numbers; a retake keeps the target's area and point, and C shows the saved picture over the new one; the magnifier draws the parts and Z pins it; Test searches the picture's own area. Ctrl+Alt+C opens Capture with the game in front. The service tells what a target already has (`capture.service.existing`)

- darbit Studio's window: closing it keeps darbit in the tray (it says so once), it opens where it was left at the same size (made to fit a screen still there), and a second `darbit app` brings the open Studio forward

- The run pill in the Qt Studio: Play hides the Studio behind a pill at the top of the screen (the bot, where it is, Pause, Stop, ⤢) that slides away until the real mouse comes to that edge and stays out of the bot's screenshots. The bot stopping or failing brings the Studio back. A darbit setting turns it off

- darbit's service (`darbit serve`): starts, pauses and stops bots whether the Studio is open or not, through one local socket with typed JSON messages and a token (`service/`). The CLI drives it: `darbit bots`, `start`, `pause`, `stop`, `status`, starting it in the background when needed. `python -m darbit` works too

- Run history in SQLite (`.darbit/history.db`): every run report line, copied as the bot writes it and queried by day and kind. The Results page reads it instead of each day's report (the week's gains no longer read seven whole reports), and `darbit history BOT [DAY]` shows a day

- Notifications from the service to a phone (ntfy, Discord or Telegram, set in `notify.toml`): a bot failed or ended, a running bot stuck with nothing in its report, and each day's summary. `darbit notify` sends a test message

- darbit Studio, rebuilt in Qt (PySide6 and QML, the `studio` extra): `darbit app` opens it. A window onto the service, so closing it stops nothing: the bot picker, the run controls, and Overview, Library, Runs and Settings, after the mockups and their design tokens in four themes. It opens on the bot shown last, and has darbit's logo in the taskbar and the tray
- The Qt Studio redesigned (Studio round 9): one place for each control, a run control that changes shape, bots in a menu or (a darbit setting) a sidebar that folds on a narrow window, New bot from the template, a git link or a folder, a Library of every asset in one grid with search, filters, sort, optional groups and an inspector (Retake, Rename, Delete, where it's used), Results with a sentence, the week's gains and a timeline, Settings by section with a save bar, and darbit settings. Pages, cards, the inspector and the save bar move into place; nothing moves while idle (0% of a core, measured), and smooth effects can be turned off. The service makes and installs bots (`bots.new`, `bots.install`)
- The action editor in the Qt Studio: an action's sections and steps read like what they do (keys, waits, picture checks, clicks, loops and ifs indented, the tape's span, calls), Play following them step by step, and sections renamed, waits changed, steps moved and removed, then saved to its file. The service reads and saves actions (`bot.action.read`, `bot.action.save`)
- The screen map (`d.Map`, `d.screens`, `d.go`): screens proved by their pictures and the moves between them; `go` finds where the game is in one look, takes the fewest moves, checks each arrived and takes a new way after a wrong turn. `darbit.testing.FakeGame` stands saved screens in for the game, so a bot's routes are tested without it
- Highlight in the Qt Studio (Ctrl+Alt+H, or the Library's button): each of the bot's pictures found on screen gets its box and score over the game, twice a second, with the bot's own matching options plus `fast`. Pictures found on the same spot are marked as look-alikes. `keymap.combo()` gives an action's keys
- The input worker: recording runs in a process of its own (`python -m darbit.worker`), started by darbit Studio and spoken to with darbit's messages over its stdin and stdout, so nothing in the Studio can delay an input. A worker that ends is started again on the next recording, and one whose Studio goes away mid-recording keeps nothing
- Polite mode (`[settings] polite = 5`): a running bot lets go of its keys and steps back at its next darbit call when the person moves the mouse or presses a key, and goes on after that many seconds without them. darbit's own input doesn't count
- Window space is an option: `[settings] space = "window"` moves and scales targets taken in the app's window with it, and searches one with no region of its own only inside the window. Screen pixels stay the default (before, every target with a window followed it). On the bench a moved, smaller window is searched in about 10 ms with `fast,grayscale`, against about 100 ms for screen pixels with `sizes`
- The recorder in the Qt Studio: Record names an action, the Studio steps aside, and a pill shows the time and steps with Checkpoint, Pause, Done and ✕; while paused, a check (a picture to wait for or until it's gone, taken with Capture on that moment, or a wait). The Library lists actions with Play, Stop, Record again, Rename and Delete (the service's `bot.actions` and `bot.action.*`). Capture's toolbar became the same pill, with a magnifier and a similarity slider after Test
- The new Studio's theme (glass dark, glass light, midnight, high contrast) is picked in darbit settings and kept for next time; `theme.toml` in darbit's settings folder still lays tokens over it
- Capture in the new Studio: the frozen screen full screen, click to box (again for bigger, right-click smaller) or drag, handles and arrow keys, Image, Region or Point, Test with each match's score, and Save. The shot stays in the Studio's process; `capture.service.use_shot` works on a saved screen instead

- The test bench (`bench/`): darbit's own search on saved screens with known answers, for accuracy and speed. Made-up cases are generated from code; real game screens live in the private darbit-bench repo, made from the screens darbit Studio saves (`bench/from_screens.py`); CI runs it. Today's baseline: right answers, but 0.4–0.8 s per whole-screen search against a 40 ms goal, a recoloured icon wrongly found, and targets at another screen size not found

- Matching options, each off until asked for, per target (`"match"` in its `.json`) or per bot (`[settings.match]`): `grayscale`, `fast` (smaller copies first, then a full-size check), `colour` (an icon in other colours isn't a match) and `sizes` (other sizes in turn when the picture isn't found). On the bench, `fast` with `grayscale` takes a whole-screen search from about 0.6 s to 15 ms with the same answers; `colour` and `sizes` fix the recoloured icon and the 1920 x 1200 targets
- The SikuliX-style API: `Pattern` (a picture with settings changed in code: `.similar()`, `.exact()`, `.offset()`, `.within()`, `.options()`), `Region` with `exists`, `find`, `wait`, `vanish`, `find_all`, `click` and the rest inside itself, `Screen(n)` for one monitor, `App(name).window` as a Region, and `d.find`
- `fast` checks its candidates at half size first and only the best at full size: 20–30% quicker with the same answers, a search inside the 1660 x 1080 panel from about 7.7 ms to 6 ms on the bench
- Loaded pictures stay in memory and their files are checked at most once a second: loading a target per search went from about 0.8 ms to 1 µs
- `settings.matcher` picks another matcher from a plugin (the `darbit.matchers` entry point)
- darbit's new logo (`assets/logo.svg`, with `logo.png` and the Windows icon `darbit.ico`): a "d" whose bowl is a target ring with the match at its centre, on a dark glass tile in the accent colours. The Studio uses it as its app icon
- Live tests on a real Windows desktop (`tests/live`, CI's `live-windows` job): screen capture, clicks, keys and text, window lookup and window space, a tape's timing, Highlight finding a picture and letting clicks through its overlay, the capture tool saving a picture pixel for pixel, the recorder pill, the listener leaving darbit's own input out, the input worker, and the Studio drawn on Windows, all on a window of the tests' own

- The Studio's Overview welcomes a first start: with no bots yet, darbit's logo and New bot, From a git link and Add a folder instead of "Not running"

- The ghost cursor (#117): darbit Studio shows a ripple where a running bot clicks and keycaps for the keys it presses, over the game, so a person sharing the PC can tell the bot's input from their own. Bots tell the Studio over a local UDP port and never wait for it; on by default, off in darbit settings

- A bot waits while Windows is locked: at its next darbit call (looked at once a second) it lets go of its keys, writes `screen: locked` in its run report and waits, then writes `screen: back` and goes on. The Overview says it's waiting and since when

- `[run] restart = 3` in a bot's `darbit.toml`: the service starts a bot that failed again a few seconds later, up to that many times an hour, then leaves it stopped. The failure's notification says which

- Old history goes: the service deletes each bot's run history, run reports and daily logs older than `[run] keep_days` (30 by default), when it starts and every six hours

- `d.area(name)` and `d.point(name)`: areas and points taken with the capture tool, used by name and placed like pictures. An area with no picture now loads as a target

- `darbit doctor [BOT]`: what would stop a bot before it starts: its darbit.toml, pictures its setup guide lists but aren't taken, display scaling unlike when the pictures were taken, its game window not open, a locked screen

- `d.record.recovered(how, why)`: a bot that gets itself going again (a rejoin, back to the lobby) says so, and each day's results count them by reason: `darbit history` and the daily summary show "rejoin x5: disconnected 3, no Play button 2"

### Removed

- v0.4's web Studio leaves `main` for the rebuild (decision 0015): the Svelte UI, the local web server and its message contract, the pywebview windows, the tray and run pill, and the `app` extra. It stays in the `v0.4.0` tag and the `maint/0.x` branch; `darbit app` says where. The logic behind its pages (projects and runs, library, Overview, results, actions, recording) stays in `server/` until the service
- The old Tk capture tool and `darbit capture` and `darbit guide`; capturing goes through the Studio. The capture session, store, engine and setup guides stay
- The placeholder modules (DXGI capture, run files, highlight, the capture API) and the keymap's unfinished functions

### Changed

- Everything that talks to the operating system sits behind small interfaces (`platform/backend.py`: Screen, Input, Windows, Listener, Hotkeys, System), with Windows' versions in `platform/win32/`. Each system's code loads the first time it's used, so `import darbit` works anywhere and another system is told plainly it isn't supported yet. The stop key, keeping the PC awake and the Studio's process handling go through the System piece instead of calling Windows themselves
- Dependabot no longer watches npm packages: the web UI left `main`
- The tests run on any system: off Windows, the platform pieces come from `tests/fake_system.py` and the tests of Windows' own pieces are left out. CI runs them on Linux too
- A bot on a system without a keyboard piece still takes the Studio's stop and pause: the stop hotkey is left off instead of ending the thread that watches both
- `main` is `1.0.0.dev0`; a bot made with `darbit new` from it follows `main` instead of a release tag

### Fixed

- The Library counted points as images: it looked for the kind `location` where the service says `point`, so the Points tab missed them
- Recorded actions showed only on the Library's Actions tab; All now lists them with the pictures, areas and points
- Capture's Test said "1 match · 1 look-alike" for a picture found once, counting the box twice. It now says found once, more than once or not at all, and how many look-alikes score under the line. The scan line sweeps the searched area again before the matches show
- Capture's magnifier showed the screen as drawn on the window, smoothed and at the window's scale, a pixel off from the mouse. It shows the shot's own pixels, the one under the mouse framed, and Ctrl+wheel zooms it from 2× to 24×
- The mouse wheel moved the Studio's pages a few points a notch, stiffly. Each notch glides 140 points; a touchpad moves them directly
- Highlight shows one picture, chosen in the Library's side panel, instead of every picture of the bot; Ctrl+Alt+H shows the last one chosen

- The Studio's Library answers at once: a tab, filter, search, sort or card used to wait 0.6 to 2.5 s for the next frame with 188 assets (every read of the library from the page copied the whole list, thumbnails and all), and now takes 20 to 40 ms. The cards fill each row, and opening or closing the inspector only narrows or widens them in place instead of moving every card to another row
- The tests never touch the real darbit folders: `DARBIT_HOME` puts darbit's own folders under one, and the test run sets it to a temporary folder. The live service test stopped the running service and left its test bots in the Studio's bot list. `ui.json` saved with a byte-order mark (Windows PowerShell) is read instead of treated as empty
- The ghost cursor costs about half as much while a bot fights (12.7% to 6.1% of a core on a 2560 x 1600 screen, about 2% with smooth effects off): its window covers only the area around its marks, not the whole screen, and a burst of keys is shown together at most ten times a second
- Observers grab only the area their pictures are searched in, not the whole screen: twice a second, that grab was most of what an idle bot did
- Each darbit process (the Studio, the service, the input worker, a bot) commits about 60 MB instead of 800 MB on a 24-thread PC: darbit keeps numpy's OpenBLAS to one thread (`OPENBLAS_NUM_THREADS=1` unless set), whose per-thread buffers it never used
- darbit Studio has its own taskbar button with darbit's icon (it was grouped with python.exe), and `darbit app --shortcut` adds it to the Start menu and the desktop with that icon (`system.name_app`, `system.add_shortcut`)
- The Studio keeps its look switches (effects, ghost cursor, sidebar) in memory: the ghost cursor read `ui.json` from disk for every click and key a bot made, about 23% of a core during a fight
- The ghost cursor stays out of screen captures, darbit's own included: its ring sat on the button the bot had just clicked, and the bot's next look saw it (`windows.keep_out_of_captures`)
- The live tests pass on a PC at 150%: Capture's saved picture may differ from the file by one colour step (some displays move colours by 1 between grabs once a Direct3D app runs), and the screenshots they save are git-ignored
- The Studio's Library says it's loading until the bot's pictures arrive, instead of "No pictures yet"
- A step left open by a bot that was killed or crashed shows as stopped on the Overview, not running: steps record their process
- `darbit doctor` and the bot template point to Capture in darbit Studio instead of the removed `darbit guide`
- Display scaling is read again on scaled screens: `scale_at` used `ctypes.wintypes` without importing it, and since the system pieces load lazily it said 1.0, so on a 150% screen every picture taken at 150% was shrunk and not found
- The Raw Input listener (the recorder, polite mode) no longer hits an access violation when it makes its window on 64-bit Windows: the module handle was cut to 32 bits
- A pre-release darbit (`1.0.0.dev0`) counts as its release when a bot's `darbit` range is checked, instead of "can't read"
- No console window on Windows when the Studio starts darbit's service, or the service starts a bot: a venv's python.exe opened one for the real Python, over the game (seen live on Windows; CREATE_NO_WINDOW doesn't work with DETACHED_PROCESS)
- Highlight's boxes sit on the pictures at any Windows display scaling (125%, 150%) and with a monitor left of the main one; they were drawn at 100% from the desktop's corner. CI checks it at 150%
- Capture boxes a picture with no border of its own (an icon on a plain background) to its edge: the box traced from its edges kept a pixel or two of background on every side, found by the live test on Windows
- Highlight, the capture window and the recorder pill are windows of their own: they belonged to the Studio's window, which hides while they're on, and on Windows Highlight's overlay never showed
- The Studio on Windows: icons drawn from symbols use Segoe UI Symbol (they came out tiny), and on a narrow window the Library's tools show only their icons and Missing and Weak only when there are some, so nothing runs off the edge
- The live tests' skip no longer skips every other test too (CI ran none for two merges)
- The service's watcher no longer crashes when a running bot's folder goes away; a test whose thread crashes now fails
- Tapes keep their timing when playing falls behind: an event more than 8 ms late moves the rest of the tape later instead of the next events going out at once, so waits and held keys (walking with W) stay as long as recorded
- Pausing a running tape and going on presses its held keys and buttons again and carries on from where it was, instead of going on with nothing held and the paused stretch played at once
- The recorder keeps the waits between inputs it got to late: their times come from Windows' message time when the moment they were read is clearly later
- Each tape notes how the recording went (`"notes"`: inputs that came in late, the latest, inputs lost), to tell a bad recording from a bad replay

### Docs

- The rebuild plan (draft): what darbit is, every feature to design for, the core API, the process layout, the Studio on PySide6 and the order of work
- Decision 0015: rebuild around a fast, swappable core; the roadmap, design page, 2026-10-25 plan and task pages move to `docs/archive/`; the code style relaxes (simple comprehensions and key lambdas are fine, bot code stays the plainest)

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
