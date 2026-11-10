# Changelog

## Unreleased

### New

- An empty state on every page that can be empty (#319): `EmptyState`, a soft glyph in a glass circle, a title, one line of why and the main action with its key, rising in with the cards. On the Library and each of its tabs (Images, Regions, Locations, Actions, and when the search leaves nothing), its Screen view, Results, the Overview before a bot's first run (`ran` in `bot.overview`), an action with no steps, Settings with nothing to set, and Scout's pill. Results opens on today: with no run yet today, it says so, with a link to the last day that has runs

### Changed

- A name too long for its place ends in "…" and shows whole on hover (#319): Scout's lines, its detail and the one landed on in its pill, gains on Results, and the bot's name in the top bar and the bot menu. They ran on past their box
- Capture's kind (Image, Region, Location) and where an image is searched are Tab stops, after the name and before the pill's buttons (#319): **Enter** or **Space** picks one and keeps the focus there, **Esc** goes back to the shot. One with the focus looks as it does hovered (`tabStops` on `Segmented`)
- Dragging a pill no longer shows circles at the edge's corners and centre: the ghost outline and the glow by the pointer show where it lands (#472)
- A pill dragged toward an edge shows a dashed ghost of itself where it lands, in its size and the form it takes on that edge, in place of the filled circle (#467). Only the part of the edge by the mouse glows, and follows it, in place of the whole edge lit (`PillGuide`; `ghost` and `pointer` on `PillPlace`, `landing` gone)
- Card thumbnails are decoded at the size they're drawn, in the screen's pixels (#230): the Library's cards, Scout's tiles and lines, and the pictures in Results' search rows (`Thumbnail.qml`). Qt decoded a picture given both sides of `sourceSize` to cover that size at the screen's scale, a 160 px thumbnail at up to 1344×336 px. They look a little softer. The Library's inspector shows the image's whole file instead of its thumbnail (`file` in `bot.library`). On a real GPU at 150% with a 175-image bot, the Studio on the Library went from about 276 MB to 225 MB (private working set)

### Fixed

- `FakeGame` fakes the mouse's position and the desktop that `approach` reads (#464): the desktop is the screen showing, the mouse starts in its bottom right corner and goes where a click or move puts it (`mouse`, and every move in `moves`). A bot's tests with `approach` on read the real cursor on Windows and failed with NotSupported on Linux

## 1.0.0-alpha.9 - 2026-11-10

### New

- `approach` (#458), a setting in pixels, 0 (off) at first: a click with the mouse already closer than that to its spot steps back that far first (on away from the spot, or up, left, right or down, staying on the desktop), then glides in. A game that sees a button's hover only when the mouse moves onto it misses a click whose mouse is already there; a retry steps back again
- **What the bot sees**, an Overview block (#316): the screen at the bot's last look with what it looked for boxed, solid in the accent with its name and score where found, dashed red at the closest spot where not, the look under it and a live time. Off until added in Customize, or placed with `kind = "sees"` in `overview.toml`. While the block is in sight the Studio keeps `watching.json` fresh and the bot keeps a 640 px JPEG of its look at most once a second (`logs/sees.json`), made on its own thread; out of sight, a look costs the bot a clock read and nothing is grabbed or decoded
- Undo for Delete and Rename in the Library, in the message at the bottom (#319). A deleted asset's files, or an action with its tape and breakpoints, are kept in the bot's `.darbit/deleted` until the next delete, and `bot.library.undelete` puts them back; a rename is taken back by renaming it back, on the bot it was done to, and the inspector follows it
- A name too long for its card shows whole on hover: Library cards, Scout's tiles, Capture's target tiles and the bot rows (#319)
- Capture's pill by keyboard (#319): from the target's name, Tab and Shift+Tab go through the pill's buttons, Enter or Space presses one, Esc goes back to the shot. A button with the focus looks as it does under the mouse; nothing changes until Tab reaches one
- Run one mode or one step of a bot instead of its round (#318). A bot lists its modes and their steps in `[modes]` in its darbit.toml; `bot.start` takes `only` (`{"mode", "step"}`), `darbit start` takes `--only MODE --step STEP`, and the bot gets it as `DARBIT_ONLY`, read with `d.only()` and `d.wants(mode, step)`. In the Studio, a mode in the Overview's Today's round shows ▶ on hover, and the command palette lists `Run only <mode>` and `Run step: <mode> · <step>`; the run pill and the run control say `only <mode>` while it runs. Play's checks and the stop-and-start question work as for a round; a failed run of one mode isn't started again by `[run] restart` (decision 0022)

### Changed

- Pills over the game (#449) sit in the screen's work area, never under the taskbar, on whichever side it is and at any size; a taskbar that hides itself keeps its room too (`system.hidden_taskbars()`). Kept places stay inside the work area when the taskbar or the screen changes. A pill stays where it's let go along its edge, and a floating card where it's let go; only a drop within 24 points of an edge's centre or a corner lands on it. Dragged, the pill's window keeps one size, so a new form eases in without a jump; let go, it glides to its place with a little spring (`studio.pillMotion`). The guide's edge light fades between edges, its corner and centre circles glide, and a filled circle follows the mouse to where the pill lands.

### Fixed

- With darbit's icon in the hidden-icons flyout (the ^ arrow), the tray panel opens outside the flyout instead of over its icons (#452): above it, or beside it when there's no room above, inside the work area on any taskbar edge. `system.tray_flyout()` looks the flyout's window up (Windows 11 and 10), only reading it
- The tray panel opens above the taskbar, inside the work area the pills use (#452): on whichever side the taskbar is, one that hides itself included, with the icon's place Windows gives in its own pixels brought into Qt's points under display scaling. It's placed again once it has opened at its size
- The Studio holds less memory (#230): the Library's thumbnails and the Screen view's shots come to QML as files in darbit's cache (`studio-pictures`) instead of data URLs, which QML copied as text with every read of the list and every Image (the pixels shown are the same); and once Scout is off, the images' pixels it read are let go (`targets.forget()` now drops the files' pixels too, `placement.forget_resized()`). On a real GPU with a 200-image bot, after the Library, Capture, Scout, Results and Settings, the Studio went from 359 MB to 274 MB (private working set) at idle
- `darbit.testing.FakeGame` fakes looking up the game's window too (`windows.matching`, `in_front`, `region`): with `window` set in a bot's settings, its tests on saved screens no longer reach the system's windows before every click and key. Looking up `settings.window` finds a fake window, always in front, with an empty area so window-space targets stay where they were taken; no other window is open
- A tape played while its window is minimised (an empty area) plays where it was recorded, instead of every place squashed into the window's corner

## 1.0.0-alpha.8 - 2026-11-09

### New

- The Studio moves (#441): a page fades in and slides up 10 px while its cards rise one after another with a little spring, and the page left fades out under it; the page and sidebar lights spring to the new choice, glowing while they move; cards and tiles lift 3 px under the mouse with a soft shadow, an accent edge and a light that follows the mouse; numbers count up, rings sweep and the week's bars grow from the bottom; the live dot pulses while a bot runs; toasts spring in and fade out. Nothing changes at rest, nothing moves while the window is hidden or minimized, and only the live dot moves on its own. **Smooth effects** off turns all of it off. Timings and curves are motion tokens in `theme.py` (`studio.motion`); `CardMotion`, `MouseLight`, `CountUp` and `LiveDot` are the shared pieces
- **Blur-through pages** and **Aurora** in darbit settings, both off at first: pages blur out and in and cards tilt into place; a slow drift of the glass themes' background light, never on battery (`system.on_battery()`)

### Changed

- Run reports, daily logs and history are kept for 14 days by default, set with `keep_days` in `[settings]` (`[run] keep_days` still works). The bot deletes its own old reports and logs when it starts writing and each new day; the service deletes old history when it starts, when it starts a bot and every six hours. Days go by the bot's `day_starts`, and today's and yesterday's are never deleted. History leaves out image looks (`exists`, `wait`, `vanish`, `find`): the Results page's problems read them from the day's report instead. An existing history loses its looks once and shrinks; on two weeks of a real bot, history.db went from 95.5 MB to 4.1 MB (decision 0021)

### Fixed

- While the Studio is hidden or minimized, a new Overview no longer redraws its page: the page shows the latest one when the window is back. The run pill's line and the tray's "may have stopped matching" still come at once (`studio.live`). The Overview also keeps its blocks when new numbers come, instead of making every block again every couple of seconds while a bot runs
- The service spent about a third of a core while a bot ran: every Overview refresh read the last 7 days of every event from the history to total the gains. It now reads only the gains (0.57 s down to 0.004 s per refresh on a week of a real bot's history)

## 1.0.0-alpha.7 - 2026-11-08

### New

- One bot that sends input runs at a time: bots on one desktop share one mouse and keyboard. The service refuses to start a bot while another one that sends input runs or is paused, with a reply naming it (`code` `input_bot_running`, `detail.running`), unless `bot.start` has `replace: true`, which stops that one cleanly first. `darbit start` says which bot is in the way and has `--replace`. A bot that never sends input says `[run] input = false` in its darbit.toml and runs alongside anything. A failed bot started again by `[run] restart` follows the same rule. `bots.list` and `bot.status` say each bot's `input`, and `bots.running` lists the running ones. A bot started without the service warns when the service runs another bot that sends input (decision 0020)
- An action played from the Studio follows the one-input-bot rule too: `bot.action.play` is refused while a bot that sends input runs or is paused, its own bot included (`code` `input_bot_running`), unless `replace: true` stops that bot first; starting a bot that sends input while an action plays or waits at a breakpoint is refused the same way, and `replace` stops the action. Recording an action is refused while a bot that sends input runs or is paused (decision 0020)
- Starting a bot that sends input, or playing an action, during a recording is refused the same way (`detail.running` has the recording with `status` `"recording"`); `replace` doesn't stop a recording. The input worker leaves `recording.json` in darbit's data folder while it records, and one left by a worker that's gone is ignored
- Recording an action is refused while the service plays one too (its bot's entry with `status` `"playing"`), with no replace. The service's new `inputs.running` lists everything sending input now: input bots running or paused, the action playing and the recording on
- The service's replies can carry a `code` and a `detail` with an error, and `ServiceError` has them; fields a client doesn't know are skipped
- The Studio asks before stopping a bot in the way: Play (the run control, F5, the command palette, the tray panel, Start anyway) while another bot that sends input runs says "fish-bot is running and uses the mouse and keys. Stop it and start my-bot?", with Cancel and Stop and start, which starts it again with `replace`. Playing an action (Play, Step through) asks the same, with Stop and play. A bot with `[run] input = false` never asks. Record refused while a bot that sends input runs says why
- The run pill shows every running bot: a line each under the shown one (a block each in a column, "Also running" floating), with its state, time and its own Pause and Stop. A bot that sends no input says "alongside" there and in the tray panel
- `Sheet`, the one frame every sheet over the Studio uses (New bot, Record, Play's checks, Stop and start)

### Fixed

- Closing the Studio to the tray or minimizing it while a bot is running or paused opens the run pill, as a bot starting does; it shows that bot, the shown one first. Showing the Studio again closes the pill

### Changed

- The tray icon opens a panel in darbit's look instead of Windows' menu, by the icon on whichever edge the taskbar is: every running bot with its state, Pause or Go on and Stop (the shown bot's Play when none runs), Capture, Scout and Record an action with their keys, Open darbit Studio, and Quit saying what it does with the running bots. A click outside or Esc closes it; a double click opens the Studio. The Go to submenu and darbit settings are no longer in the tray. `MenuLine` shows a line's keys
- Quitting the Studio stops every running bot, cleanly through the service (letting go of every key), instead of leaving them with nothing to control them. **Bots go on after quitting** in darbit settings keeps them running. The tray's Quit says which: "Quit and stop fish-bot", "Quit and stop 2 bots" or "Quit (bots go on)"

## 1.0.0-alpha.6 - 2026-11-08

### Fixed

- Capture's tiles in the side column keep the active one in sight: the column had no width until the window's layout gave it one, so tiles placed before then stacked one a row, and when they reflowed into two the list kept that offset and stepping to another target scrolled it the wrong way. The column has its width from the start
- `darbit bench`'s speed gate no longer fails on a slow CI runner: each search is judged by its fastest repeat instead of its median, and against the run's own speed (the median of every search's time over its baseline), so a machine that runs the whole job 2 times slower passes while one search much slower than the rest still fails. A whole run more than `--machine-slower` (3) times slower fails. Results and the table have the fastest time too, and `--save-baseline` writes it; darbit's bench/baseline.json holds CI's fastest times. Baselines saved before hold medians, which only makes the gate a little looser until they're saved again

### New

- `DARBIT_NO_REAL_INPUT=1` turns real input off: every click, key, mouse move, hold, scroll, drag, app open, close or focus and screen grab raises `RealInputOff` naming the call, instead of touching the PC. Read-only calls (the cursor, open windows, `App.running`, monitors) still work, and `darbit.testing.FakeGame`'s fakes are used first. A bot's tests turn it on with one line in their conftest.py, `pytest_plugins = ["darbit.testing.no_real_input"]`, whose `real_input` fixture turns it back on for one test. darbit's own tests run with it on, except the live tests

### Changed

- `darbit.testing` is a package; `from darbit.testing import FakeGame` is unchanged. FakeGame also stands in for the game's window: bringing `settings.window` to the front does nothing while it runs
- `App.open` goes through the platform's Windows piece (`windows.launch`), like closing and focusing

## 1.0.0-alpha.5 - 2026-11-08

### New

- Reading text on screen: `d.read(where)`, `d.read_number(where)` (`4.99M`, `126.62B`, `1,234`, `12%`, `1.5k`) and `d.read_time(where)` (`02:31`, `1:02:03`, `2m 30s`, in seconds), also on a Region and a Match. `where` is a Region, a Match, a named Region or a named Image. A Region's .json can say what it holds (`"text": "digits"`), and a read uses only those characters. Unreadable or unsure text is None. The reader is RapidOCR with its bundled models, in the new `ocr` extra (`pip install "darbit[ocr]"`); a single line reads in about 10 ms. Each read is logged and recorded with its confidence, `[settings.read]` has preparing options (upscale, invert, threshold, lines), and `darbit bench` judges and times `[[read]]` entries (decision 0019)
- Capture's pill lists the targets taken on the shot as tiles (each one's image, name, kind and, after Test, its score or look-alikes): a stack that opens into one row of tiles scrolling sideways in the pill on the top and bottom edges, and two columns scrolling up and down on the sides and floating. A tile makes its target the active one, ✕ drops it (Ctrl+Z brings it back), and the stack folds them away
- Capture takes several targets on one frozen shot when taking new ones: a box made away from the ones taken starts another target, each named to start with the time it was taken (SikuliX's way) so a batch can be saved and renamed later. A click on a box makes it the active one, highlighted, with its name field beside it; the kind, the handles and the arrows act on it, N and Shift+N step through them, and A starts a new one. Names show on the box under the mouse. Test checks every image on the shot at once (each one's score and look-alikes, on its box), Save saves them all, and Ctrl+Z undoes each change. A retake, the guide and the recorder's checks still take one
- Every pill over the game (the run pill, Capture's, Scout's and the recorder's) can be dragged to any screen edge: a row on the top and bottom, a labelled column on the sides, snapping to each edge's centre, its corners or near the centre, and still hiding into its edge; dragged firmly into the middle it floats as a small card with more detail and Dock. While it's dragged it tilts, takes the shape it will have, and the edge it goes to lights up with its snap places. Each pill keeps its place for next time, per screen, with display scaling
- Capture's arrows and Ctrl+arrows speed up while held: a press still moves or resizes exactly 1 px (Shift: 10), and after about half a second of holding it goes faster, up to a top speed, until the key is let go
- Capture resizes the image or region picked by dragging any of its edges or corners, like cropping: the cursor shows which way, the readouts and the magnifier follow, and Ctrl+Z takes a drag back
- Capture can retake a target on a saved screenshot instead of the screen now: a failure's on Results, and a screen's last shot in the Library's Screen view (Retake on this shot). The image is cut from that shot at its own pixels; a lossless copy beside a JPEG is used first, and Capture says when the shot is JPEG and so a little softer. A retake on a screen's own shot keeps the other targets placed on it, and the shot isn't encoded again
- Scout's pill in three forms: docked on the top or bottom, a group filter and a strip of the group's images stepped through with N and Shift+N, the one landed on boxed on the game with what's wrong and its retakes (on the shot where it was seen, or on the screen now); docked on a side, a ring and the groups in a list, a line hovered showing its retakes; floating, a grid of every image coloured by its state, one clicked shown large beside the shot where it was seen with its score against what it needs. The Regions and Locations of the screens showing are drawn on the game. A retake hides Scout while Capture is open and brings it back after

### Changed

- darbit depends on `opencv-python-headless` instead of `opencv-python`: the same OpenCV without its GUI part, which darbit doesn't use, and the one the `ocr` extra needs, so an environment has one `cv2` instead of two that overwrite each other
- The bench baseline has CI's times for the reads, so a slower read fails CI, and so does a read in the baseline that didn't run because the `ocr` extra is missing
- A retake in Capture keeps what a target's .json says besides its place: its similarity, matching options and, for a Region, its `text` and reading options
- Highlight is Scout: it searches every image of the bot while the game is played by hand and keeps a record for the session of each one, seen (when, best score, on which screen), weak (found under what it needs, or with a look-alike) or not seen yet, with the latest shot of each screen it saw for a retake on it. Its pill says "Scout: 31 of 40 seen"; floating, it has Reset the session. Its key is Ctrl+Alt+S (`scout.toggle`); a key set for `highlight.toggle` still works. The Library's and Results' Highlight buttons are Scout and land on their image

### Fixed

- Studio tests no longer fail now and then: they run with effects off, so a pill sits where it ends up rather than where its slide happens to be, and no pill tucks away on the clock in a slow run. The resize test grabbed a region's edge under Capture's pill and its tiles, and only passed while the pill was still widening; the tests that only check the windows draw without a warning still run with effects on
- Renaming a target in the Library renames it in the screens' saved boxes too (`.darbit/screens/<screen>.json`), so the Screen view and bench cases made from those screens keep its box

## 1.0.0-alpha.4 - 2026-11-08

### New

- darbit Studio's Play runs darbit doctor's checks first: with a problem, a sheet shows every check with what it found and how to fix it (Take them opens Capture on the targets not taken), with Cancel, Check again and Start anyway; with none, the bot starts at once
- darbit Studio's Results shows a failure opened as the screen when it stopped, with the closest match of the image it waited for boxed and scored, beside that image (best against what it needs) and the steps before it; under the screen, Retake on that screen or on the screen now
- darbit Studio's Overview has a Recoveries block: how often the bot recovered today, the most common reason and the last one, or that it hasn't had to; darbit's default layout ends with it, and `overview.toml` places it with `kind = "recoveries"`
- `d.keep_trying` takes `back_timeout`: how long the go-back to `back_to` waits for each screen, finding where the game is included; None keeps `settings.timeout`, so a bot that's clearly lost recovers sooner

### Changed

- darbit doctor's checks carry their fix apart from what they found (`found`, `fix`), and the targets not taken as a list (`missing`), in its output and the service's `bot.doctor`; the `pictures` check is `targets` and its words say image

### Fixed

- Capture's magnifier follows the mouse after a click and while a box is drawn, instead of staying where it was
- A new shot of a screen in Capture no longer keeps other targets' boxes from older shots of it: `.darbit/screens/<Screen>.json` holds only the boxes taken on the shot saved beside it, so the Library's Screen view and `darbit bench --from-screens` don't place them where they no longer are

## 1.0.0-alpha.3 - 2026-11-08

### New

- `d.keep_trying` takes `back_to`, a screen of the map: after a failure it goes back there and tries again, and only calls `recover` when that doesn't help; Results counts each go-back apart from the rejoins
- Results' data: each problem has the last steps before its failure (clicks, looks, the steps inside it, moves between screens), and darbit Studio can retake an image on a failure's screenshot (`retakeOn`), cut to the main screen
- The service's `bot.doctor`: darbit doctor's checks on a bot and how many are problems; darbit Studio asks for them (`checkBot`) for its Start
- The Overview's data counts today's recoveries (`d.record.recovered`): how many, the most common reason, the last one and each way the bot recovered, for an Overview block

### Fixed

- The service's action player and recorder set a bot up for each run without piling up its held "settings from darbit.toml" lines: each setup keeps only its own
- Only a running bot writes to its log: importing darbit in a bot's folder (its tests, `darbit status`) keeps the "settings from darbit.toml" line, and a version warning, until the bot writes its first line
- `darbit bench --from-screens .` names the cases after the bot's folder instead of an empty name

### Docs

- `AGENTS.md`: how work is done (check before claiming, complete plans, UI choices from rendered options, extend shared parts, Image/Region/Location), working in parallel (Studio and core areas, worktrees, bots asking through issues), and live testing on a desktop
- Design system: describes the Qt Studio's shared components, themes, surfaces and motion as they are, instead of the old Svelte UI and the dated review rounds

## 1.0.0-alpha.2 - 2026-11-08

### New

- `darbit bench`: the test bench as a command, so any bot can measure darbit's search on its own saved screens (`--from-screens` makes the cases from what darbit Studio saved). `--baseline` fails a run when a search gets more than `--slower` (2) times slower; CI checks the made-up cases against `bench/baseline.json`. darbit's CI no longer reads a private repo of game screens: a bot's screens stay with the bot (`bench/run.py` and `bench/from_screens.py` are gone)

### Changed

- CI builds the docs site (strict: a broken link fails) and the wheel on every PR, so what used to break only after merging shows before; uv's cache in every job, and a new push to a PR cancels its older run. Two doc links that pointed outside the site go to GitHub
- The PR rules are checked: `pr-rules` fails a PR without `Closes #<issue>` or a `CHANGELOG.md` line (unless labelled `skip-notes`), pre-commit refuses a commit on `main`, and issues opened from the forms go on the board

### Fixed

- `darbit bench --from-screens` copies the shared region an image is searched in, so its case loads
- The release workflow installs the Studio extra before running the tests, as CI does: without it the live tests didn't load and no release was made

## 1.0.0-alpha.1 - 2026-11-07

### New

- An image that may have stopped matching: when the last two failures or more all came down to the same image, the Overview says so with Retake, the tray shows a Windows notification once, and `notify.toml` channels get it (`failing = true`). It used to take someone reading the logs (`problems.failing`)

- Highlight's pill is the shared pill, like the run pill: found count and time, look-alikes as a warning, ✕ to hide and ⤢ for the Studio, sliding away at the top (`HighlightPill.qml`). It was drawn by hand, thinner, as one long line

- What every bot needs, moved out of one bot (decision 0018): `d.keep_trying` runs a step until it goes through, recording each `d.Failed` or observer interrupt and recovering in between (`runtime/retry.py`); `d.config()` reads a bot's `settings.toml` and `config.toml` as `cfg.section.key` (`runtime/config.py`); `lag` makes every search's wait and every `d.sleep` longer for a slow game or PC; `State.per_day` and `State.per_week` are counters that start over by themselves and show their ring

- Decision 0018: what belongs in darbit and what in a bot, and the rule in `AGENTS.md`

- Edit in the run control: opens the bot's folder in VS Code when it's installed, else in the file explorer

- The command palette (Ctrl+K) finds anything the Studio can do, and darbit settings changes the keys: only the ones the Studio really goes by, refusing one already taken, working at once. The Studio's shortcuts now come from the keymap (`keymap.set_key`, `studio/shortcuts.py`)

- The Library's Screen view: each screen's last shot from Capture with the targets taken on it in place, in their kinds' colours; a click opens the side panel, and the search dims the others

- The action editor's breakpoints and stepping: click the dot beside a step to stop there, Step through stops at the first line, and while stopped, Next line and Go on. The service's `bot.action.breakpoints`, `bot.action.step` and `bot.action.resume`

- One look, kept by a test: every text field is `Field` and every menu `MenuPanel`, panels use one solid colour (`colors.solid`, also the ghost cursor's labels and Highlight's bar over the game), the kinds have their own colour tokens, and `docs/style/ui/design-system.md` lists the components. `test_the_studio_keeps_one_look` fails on one drawn by hand

- Errors say what happened and what to do: Capture's saves and mistakes in plain words (a look-alike names the fix), the toast shows a whole reason and stays long enough to read, the Library explains Missing and Weak in its side panel, and the Overview's problem banner uses the Results page's explanation

- Capture asks where an image is searched: the whole screen, a shared region (pick one, or share the region just drawn under a name), or a region of its own. Capture closes after a save when nothing is left to take

- Capture's motion: a shutter's flash when the screen freezes, boxes that glide to the next bigger or smaller one, a region's outline in dashes that march while it's picked, faint guide lines through the mouse across the screen, and a green pulse on what was just saved. A retake opens named and on its kind (a test keeps it so)

- The Overview is blocks (round 14, decision 0017): the bot's author lays out the default in `overview.toml` and adds blocks of their own with `d.show` and `@d.block`, and its actions become buttons; Customize lets the person drag blocks around, resize them, take them off and add any from a gallery, kept per bot with a way back to the bot's layout. The service's `bot.overview` serves the catalog, the layout and each block's data

- Problems explained (round 13): the Results page groups the day's failures by likely cause (something covered the game, an image looks different now, an image wasn't on screen, the bot's own reason) with a plain sentence of what the bot saw, and opens each into the searches that ran out before it, the screen when it stopped, and Highlight, Retake, the screenshots or Not a problem (`server/problems.py`, from what the run report already holds). The Overview's setup line no longer says the bot can't run while it does

- The bot's Settings redesigned (round 12, A with B's help panel): one row per setting with a control made for its type (switch, stepper, slider for a range, list, field), section cards in two columns on a wide window, search with counts and change dots, ↺ back to a default, and a panel that explains the setting under the mouse. The controls are shared components (`Switcher`, `Stepper`, `ValueSlider`, `Dropdown`); the Studio page's switches use `Switcher` too

- Images can share a region: an image's `region` can name a region target (`"region": "Bag.List"`), and moving that region moves every image searched in it. Capture's **Saved ▾** (with Region picked) lists the bot's regions, shared ones first, then other images' own to copy; pointing at one shows it on the screen (`capture.service.regions`, `core.targets.shared_region`)

- A bot's day can start at another time than midnight: `[settings] day_starts = "03:00"`, or `"00:00 UTC"` for a game that resets at midnight UTC. The run report and log files, history, the Studio's Overview and Results, and the daily summary go by it (`darbit.days`); the Results timeline runs on past midnight

- One set of names everywhere: **image**, **region** and **location** (the Studio said picture, area and point). Each target's settings file names its `kind`; the Library sorts by it (`core.targets.kind_of` works it out for files from before), and `darbit kinds BOT` writes it in. An image's inspector says its region and location, the defaults too: the whole screen and its centre
- Capture works on the kind picked in its pill (Image, Region, Location; 1, 2, 3 or Tab): a click or drag makes it, and the handles, arrows, drag-to-move and Delete change it. The pill is solid instead of see-through, hides fully, and shows a message only for a few seconds instead of a standing hint
- One pill for every tool over the game (`FloatingPill.qml` in `PillWindow.qml`): Capture's, the recorder's and the run pill. The recorder's pill now hides like the run pill (`studio/hiding.py`, which the run pill's code became)
- The tray menu holds the shown bot (its state, Play or Pause and Stop), the Studio's pages, Capture, Highlight, Record, darbit settings and Quit, built fresh each time it opens

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

- The `front` setting: made for one bot's rejoin, and nothing uses it. `window` still comes forward before input

- v0.4's web Studio leaves `main` for the rebuild (decision 0015): the Svelte UI, the local web server and its message contract, the pywebview windows, the tray and run pill, and the `app` extra. It stays in the `v0.4.0` tag and the `maint/0.x` branch; `darbit app` says where. The logic behind its pages (projects and runs, library, Overview, results, actions, recording) stays in `server/` until the service
- The old Tk capture tool and `darbit capture` and `darbit guide`; capturing goes through the Studio. The capture session, store, engine and setup guides stay
- The placeholder modules (DXGI capture, run files, highlight, the capture API) and the keymap's unfinished functions

### Changed

- Everything that talks to the operating system sits behind small interfaces (`platform/backend.py`: Screen, Input, Windows, Listener, Hotkeys, System), with Windows' versions in `platform/win32/`. Each system's code loads the first time it's used, so `import darbit` works anywhere and another system is told plainly it isn't supported yet. The stop key, keeping the PC awake and the Studio's process handling go through the System piece instead of calling Windows themselves
- Dependabot no longer watches npm packages: the web UI left `main`
- The tests run on any system: off Windows, the platform pieces come from `tests/fake_system.py` and the tests of Windows' own pieces are left out. CI runs them on Linux too
- A bot on a system without a keyboard piece still takes the Studio's stop and pause: the stop hotkey is left off instead of ending the thread that watches both
- `main` is `1.0.0.dev0`; a bot made with `darbit new` from it follows `main` instead of a release tag
- Pre-releases of the rebuild are tagged `v1.0.0-alpha.N` (package `1.0.0aN`) and marked as pre-releases on GitHub; `darbit new` on one pins its tag (`bots.release_tag`)

### Fixed

- A stopped bot ends with one line saying what stopped it (the stop hotkey, or Stop in the Studio, the tray or `darbit stop`) and exit code 0, instead of a traceback that always blamed the hotkey; a hotkey stop no longer counts as a failure

- A retake opens Capture with the image's name filled in again: Capture left out what was taken already, which is right for the setup guide but emptied a retake. Capture's Test also starts at the score the image needs (its own similarity, else the bot's), not 0.90

- The Library and Highlight on screen show the score an image needs as the bot goes by it: its own similarity, else the bot's from `darbit.toml`. The Library said 0.90 and Highlight 0.7 for an image without its own

- The service and its bots no longer end with the program that opened the Studio. A terminal or an editor that keeps its processes in a Windows job ended them all when it closed, with nothing in the logs; the service now leaves that job when it starts (`system.start_on_its_own`)

- Less memory in the Studio: a page is made the first time it's shown, hidden windows give back their graphics memory (the Studio is hidden for as long as a bot runs), and Capture's shot no longer stays in Qt's image cache
- `test_a_tape_plays_every_event_on_time` failed main now and then: CI's shared machines stall for tens of ms. It keeps 10 ms on a real PC and allows 40 ms on CI, with three tries
- The Library tagged images with their region and location, so the Regions tab was full of images; a region is a place of its own that images name, and only regions show there now
- A retake that boxed the image before its name was typed lost the target's region and location; typing a known name brings them back where none is made yet
- The Studio stepped aside behind the run pill only on its own Play; the shown bot starting anywhere (the tray, the command line, the service, a schedule) does it too, and opening the Studio on a bot already running doesn't
- A Studio loaded with a connection of its own (a test's, or a script drawing a page) started a real darbit service in the background, and left it running; only the Studio's real connection starts the service now
- Target settings files written on Windows had Windows line endings; they're written with LF, like the repos keep them
- The Library's Actions tab was always empty: its property was named `onActions`, which QML reads as a signal handler. A test now checks no QML property is named that way. Actions also come first under All

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

- Examples, docstrings, guides and Capture's name placeholder use neutral names (`Menu.Start`, "Daily quest", `my-bot`) instead of one bot's (decision 0018)

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
