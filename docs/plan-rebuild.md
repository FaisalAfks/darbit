# darbit rebuild plan

Draft, 2026-10-30. To be reviewed and changed before any code. Decisions so far are in section 15.

darbit is rebuilt around a fast, swappable core, with the Studio as a thin client over it. This page says what darbit is, every feature it has to be designed for from the start, how it's built, and in what order.

## 1. What darbit is

**darbit is a Python library for automating any app from what's on its screen, with an optional Studio to build, run and watch bots.**

- The **library** (`darbit`) is the product: SikuliX for Python. Everything else serves it.
- The **Studio** is a companion app, like the SikuliX IDE plus a bot manager: capture, record, run, watch results.
- The **CLI** is a set of entry points (`darbit run`, `darbit app`, `darbit capture`), not a product of its own.
- **ad-bot** (Anime Dimensions on Roblox) is the first real bot and the test of every milestone.

## 2. Principles

1. **The engine before the Studio.** A feature goes into the Studio only once the core does it well.
2. **Every detection change is a setting, never forced.** Faster or smarter matching (grayscale, a downscaled first pass, sizes, OCR, window space) is an option per picture or per bot. The default stays what works today: full-colour template matching at the picture's own size.
3. **Screen pixels are the default.** Apps automated full screen don't need anything else. Window space (positions measured in the app's window) is an option to build, test and compare, never assumed.
4. **Swappable pieces.** Screen grabbing, input, windows, matching and text reading sit behind small interfaces, with Windows done first and macOS and Linux later.
5. **Reuse before building.** A library that does the job well is used; darbit's own code is the part nobody else has.
6. **Speed is measured.** Each speed goal in section 9 has a number, and CI checks it.
7. **Small and done beats big and half done.** No placeholder modules: future work is an issue, not a stub file.

## 3. Every feature to design for

Each feature below has to fit the architecture from the start, even if it's built later. "Have" means it exists in the current code (v0.3 to #132) and is carried over; "Planned" means it's in the ideas, the roadmap or the task pages.

### Finding things on screen

| Feature | Status |
|---|---|
| Named targets: images, points and areas as one kind of thing, each with its own settings file | Have |
| A search region per image, with a whole-screen fallback as a setting | Have |
| Similarity and click offset per target (default: the centre) | Have |
| Single-colour images matched by colour distance | Have |
| Targets that follow their window and rescale with display scaling | Have (placement), to be rebuilt as the window-space option |
| Nearby sizes tried when a resized target isn't found, and the size that worked kept | Have |
| Grayscale matching, a downscaled first pass, multi-size search, feature matching | Planned, each an option |
| Masks: parts of an image ignored when matching, then masks of any shape | Planned (rectangles were tried) |
| Text targets (OCR), read or searched, alone or with an image | Planned |
| Colour at a point, an area changing | Planned (checks while recording) |
| Element targets through the app's UI tree; web pages by CSS selector | Planned (tried before) |
| One `find` for an image, text or selector | Planned |
| Wait until a match stops moving before clicking (menus mid-animation) | Planned |
| Targets that move (a slider) or appear anywhere in an area (cards in a grid) | Partly have |
| One screen capture per check, shared by every target waited for | Have |
| A faster screen capture (DXGI) | Planned |

### Input

| Feature | Status |
|---|---|
| A gliding mouse like SikuliX, so games register the hover | Have |
| Keys by position on any keyboard language; text typed as text | Have |
| Press, hold, release, combos (`shift+e`), the wheel both ways, drags | Have |
| Relative mouse moves (`move_by`) for games that hold the cursor | Have |
| Every held key and button let go on stop, pause, failure or a forced end | Have |
| Pause when the mouse is moved by hand while a bot runs | Planned |
| A clear error when the game runs as admin and input is blocked | Planned |
| Touch and controller input | Planned |

### Watching and safety

| Feature | Status |
|---|---|
| Observers: react when something appears, vanishes or changes; interrupts | Have |
| A watcher that catches errors (disconnected, teleport failed) instead of checking everywhere | Have (observers) |
| The stop hotkey; pause and stop from the Studio (control folder) | Have |
| Keeping the PC awake while a bot runs | Have |
| A `doctor` check before a run: window size, display scale, missing targets, settings | Planned |
| A recapture check after a game update: which targets no longer match | Planned (Check, Test on screen) |

### Bots and projects

| Feature | Status |
|---|---|
| A bot project: settings, assets, actions and code in one folder | Have |
| `darbit new`, `install` (from a git link), `run`; bots pinned to a darbit release | Have |
| A settings schema that becomes a form in the Studio | Have |
| Setup guides: an ordered list of pictures to take for new users | Have |
| `d.step`, `d.record`, `d.record.gain`, `d.progress`, `d.plan`, `d.next` for what a bot shows | Have |
| State that survives restarts (`d.State`) | Have |
| A screen map: each screen's recognizer and the moves between screens, so a bot asks to get somewhere and darbit routes and recovers | Planned (ad-bot's `screens/` leans this way) |
| A dry run: the schedule against the clock with no input sent | Planned |
| Replays as tests: a bot run against saved screens, without the game | Planned |
| One config per account or PC, so the same bot runs elsewhere | Planned |
| Bots in any language | Planned |

### Recording and actions

| Feature | Status |
|---|---|
| Actions as Python files (`@d.flow`), read and written by the Studio through `ast` | Have |
| The recorder: every key, button, wheel notch and mouse packet on one clock (tapes) | Have |
| Held cursor (camera) replayed as raw counts, a free cursor placed exactly | Have |
| Checks added while paused: a picture to wait for or until it's gone, a wait | Have |
| Checkpoints: each part saved as its own action with its own tape | Have |
| Re-record one action, Rename (with every caller), Delete | Have |
| Pausing lets go of held keys and leaves the pause out | Have |
| Timed actions (`@d.flow(timed=True)`) keeping to the recorded schedule | Have |
| Start a recording on a picture (the dimension's start screen), so playback lines up with the game | Planned, with the scheduled Dim macro |
| Recording onto the screen map: a recording becomes a move between screens, with checks | Planned |
| The flow editor: sections, steps, calls, Play with breakpoints and stepping | Have |
| Custom steps with `@d.action`, shown in the editor's palette | Planned |
| Flows with variables, if and loops; flows calling flows with inputs | Partly have |
| Grid harvest: scroll a grid menu and save every cell as a picture | Planned |
| Characters named from the bag's side panel, one icon per character reused everywhere | Planned |

### Capture

| Feature | Status |
|---|---|
| Freeze the screen; click to box what's there (again for bigger, right-click for smaller) | Have |
| Edit the box by mouse and keys, 8 handles, scaling, nudging; exact number fields | Have |
| Image, region and point in one view; Shift+drag for the region, Ctrl+click for the point | Have |
| A magnifier that follows the mouse | Have |
| Test: find the boxed picture in its region and mark every match with its score | Have |
| Snapping to edges and guide lines | Have (edges), planned (guides) |
| The setup guide's next-picture bar and Ctrl+Alt+C to freeze again | Have |
| Highlight: what's found on screen right now, with scores | Planned |

### Studio

| Feature | Status |
|---|---|
| Bot picker (dropdown or sidebar), pages: Overview, Results, Library, Settings | Have |
| Play, Pause, Stop and Edit; the run pill while a bot runs | Have |
| Closing keeps darbit in the tray; the window remembers its size and place | Have |
| Overview in blocks anyone can rearrange, filled from what the bot records | Have |
| Results: a summary sentence, gains and progress, a whole-day timeline, problems with Retake | Have |
| Library: every asset type, grid and Screen view, inspector, Test on screen, Retake, Rename, Delete | Have |
| Settings: sections, search, defaults, a save bar | Have |
| Themes (glass dark, glass light, midnight, high contrast, custom), a remappable keymap, a command palette | Have |
| A second launch brings the open Studio forward | Have |
| See a run live and control it from a phone; notifications (Discord, ntfy, Telegram) and a daily summary | Planned |

### Around the tool

| Feature | Status |
|---|---|
| A VS Code extension: pictures shown on hover, go to target, capture and record commands | Planned |
| An MCP server, so an AI agent can use darbit; an agent records its steps once, then the flow replays | Planned |
| macOS and Linux | Planned |
| A Studio installer and a single executable | Planned |
| A registry of bots | Planned |
| Public, MIT or Apache-2.0, open to contributions | Have |

## 4. Core library

### The API, the SikuliX way

Everything starts from a **Region**:

```python
import darbit as d

game = d.App("Roblox").window  # a Region
menu = d.Region(442, 277, 1656, 1083)  # screen pixels, the default
play = d.Pattern("Lobby.Play").similar(0.85).offset(10, 0)

if game.exists(play, timeout=3):
    game.click(play)
d.click("Lobby.Play")  # the short form: the whole screen, the picture's own settings
```

- **Region, Location, Match, Pattern, Screen and App**, with `find`, `find_all`, `exists`, `wait`, `vanish`, `click`, `double_click`, `right_click`, `hover`, `drag`, `type`, `write`, `press`, `hold`, `release`, `scroll` and `observe`.
- A Pattern's settings come from its picture's file and can be changed in code.
- Not finding something returns `None` or `False`, never an error.
- The short `d.click("...")` form stays for simple bots.

### Swappable pieces

Each is a small interface with one class per system, picked when darbit starts:

| Piece | Windows (first) | Later | What it does |
|---|---|---|---|
| `Screen` | mss, then DXGI as an option | mss on macOS and Linux | grab pixels, monitors, display scaling |
| `Input` | SendInput | Quartz, X11 or uinput (through pynput where it fits) | mouse, keys, wheel, relative moves |
| `Windows` | Win32 | pywinctl | find, focus, move windows; their client area |
| `Listener` | Raw Input | pynput | real keys and mouse for the recorder and the run pill |
| `Hotkeys` | RegisterHotKey | pynput | global shortcuts |
| `Matcher` | template (default) | grayscale, downscaled first pass, multi-size, features | find a picture in pixels |
| `Reader` | RapidOCR or Tesseract | | read text in an area |

**Plugins** add matchers, readers, tools and Studio panels through Python entry points (`darbit.matchers`, `darbit.readers`, `darbit.tools`).

### Matching

- **Default:** full-colour template matching at the picture's own size, in its region, exactly as now.
- **Options, per picture or per bot**, each measured on the test bench before it's recommended:
  - grayscale;
  - a downscaled first pass with a full-colour check of the candidates;
  - sizes around the expected one;
  - feature matching;
  - masks.
- **Pictures are loaded once** and kept in memory with their resized copies, reloaded only when the file changes.
- **One screen grab per scan,** shared by every target waited for.

### Positions

- **Screen pixels by default.**
- **Window space as an option** (a setting per bot): pictures, regions and points are kept relative to the app's window and scaled with it. It's built, tested against screen pixels on the test bench and on ad-bot, and kept only if it proves itself.

## 5. How it runs

| Process | What it does |
|---|---|
| **The bot** | the bot's own Python with its pinned darbit |
| **The service** (`darbit serve`) | starts, stops, pauses and schedules bots; keeps the run history; runs whether the Studio is open or not |
| **The input worker** | recording and tape playback, apart from the UI and Python's one-thread-at-a-time limit |
| **The Studio** | a window onto the service: nothing is lost or left running when it closes |

- **Between them:** one local socket on 127.0.0.1 with typed JSON messages, defined once in Python. Any language can connect, so a phone bridge, the VS Code extension or MCP can use the same channel later.
- **The input worker** is a Python process running the Raw Input listener and tape playback, so nothing else in darbit can slow it down.
- **Stopping a bot** asks it first (its next darbit call stops cleanly, keys let go), then ends its whole process tree.
- **Several bots at once:** the service runs any number of bots, each with its own window (or account, or monitor) to work on. Two bots never share a window.

## 6. Files

| What | Where |
|---|---|
| The bot's settings | `bot.toml`, one file with types, checked by pydantic; one override file per PC |
| Pictures | `assets/`, each with its settings, its coordinate space and an id |
| Picture names as code | a generated `assets.py` (`A.Lobby.Play`) for autocomplete; a rename updates every use |
| Actions and tapes | `actions/<name>.py` and `actions/<name>.tape.json` |
| Run history | SQLite in `.darbit/`: steps, gains, failures, screenshots; queries instead of re-reading a day's file |
| Screenshots | JPEG or WebP, with a size cap |
| Studio settings | `%APPDATA%\darbit` (platformdirs) |

## 7. Studio

- **PySide6 with QML:** the screens are written in QML (Qt's declarative UI language, built for styled and animated interfaces and drawn on the GPU), with Python behind them for the data and logic. One process for the UI.
- **Native overlays** for Capture, Highlight, the recorder bar and the run pill: real transparency and click-through on every system, screen pictures shown directly with no frames sent anywhere.
- **The tray** through `QSystemTrayIcon`.
- **Pages read from the service and SQLite,** and update from the service's events, not by polling.
- **The design system** carried over as QML components: the same tokens, themes and keymap.
- The current Svelte Studio's pages, decisions (0013) and mockups are the reference for the new one.

## 8. How bots are written

- **Plain Python on the core API,** as now.
- **A screen map** (planned): each screen declares the pictures that prove it's showing and the moves to other screens. `d.go("Speed Raid")` routes there from wherever the bot is and recovers from the unexpected.
- **Actions and tapes** for what's easier recorded than written.
- **Offline tests:** a bot runs against saved screens of each game screen, without the game.

## 9. Speed goals

| What | Goal |
|---|---|
| One search in a region | under 10 ms |
| A whole-screen search (2560 x 1600) | under 40 ms by default, less with options |
| A running bot, idle between checks | under 5% of one core |
| The Studio, idle | under 2% of one core, under 200 MB |
| Tape playback | every event within 2 ms of its time |
| Recording | no mouse count lost |

## 10. Engineering

- **Code style:** idiomatic, readable Python: small functions, clear names, a summary at the top of each module, type hints, comments that say why. Simple comprehensions and key lambdas are fine; clever one-liners aren't. ruff checks it, pyright is strict for the core.
- **Tests by layer:** pure functions (matching, placement, planning) tested directly, interfaces tested with fakes, a few real runs only when allowed.
- **The test bench:** saved screens from real games with the expected matches and times, kept in a private repo that CI pulls with a token. The public repo keeps only small made-up screens. CI checks accuracy and speed.
- **CI on Windows, macOS and Linux** once those systems are in.
- **Profiling:** `darbit run --profile` shows where the time goes.
- **Packaging:** a wheel for the library; a Studio installer (Briefcase or PyInstaller) that brings uv for the bots.
- **Paperwork kept light:** issues and milestones for the work, a decision record only for a real fork in the road, the changelog at release time.

## 11. Reused, not built

| Job | Library |
|---|---|
| Matching and image work | OpenCV |
| Screen capture | mss |
| Input and listeners off Windows | pynput, pyobjc, python-xlib |
| Windows off Win32 | pywinctl |
| Reading text | RapidOCR or Tesseract |
| Settings | pydantic |
| Scheduling | APScheduler |
| Run history | sqlite3 |
| Studio | PySide6 (QML) |
| Bot environments | uv |
| Ideas for the API | SikuliX, and Lackey (an older Python take on the SikuliX API) |

## 12. What's carried over and what's dropped

- **Carried over** (moved behind the new interfaces): matching and placement, the input code, Raw Input listening, tapes and the recorder logic, the flow file reader and writer, the player, observers and interrupts, the settings schema's behaviour, setup guides, the dashboard and results logic, the design tokens and every Studio page design.
- **Dropped:** the old OpenCV capture tool (`capture/session.py`, `overlay.py`, the old guide window), the placeholder modules, the local web server and its message contract, the pywebview windows and the thread-switching and busy-wait workarounds the process split makes unneeded.

## 13. Order and done-tests

| Milestone | Content | Done when |
|---|---|---|
| **1. Core** | Region, Pattern, Location, Match, Screen, App; the interfaces with Windows backends; template matching as the default and the first options; pictures cached; the test bench | the test bench passes and meets the search goals, and every current test is ported |
| **2. ad-bot on the core** | ad-bot ported to the new API; window space tried against screen pixels | ad-bot runs a full day unattended, and window space has a measured yes or no |
| **3. Service and history** | `darbit serve`, the input worker, SQLite history, stop and pause that always work | a bot started, paused and stopped from the CLI and a phone notification, with its history queryable |
| **4. Studio** | PySide6/QML: Capture and the Library first, then Overview, Results and Settings, then the recorder, actions and the editor | every current Studio feature works, within the Studio speed goals |
| **5. Screen map** | screens, moves, `d.go`, recording onto the map, offline tests | a bot's mode is written as moves on the map and tested without the game |
| **6. More systems** | macOS and Linux backends, CI on all three | the test bench and a sample bot pass on all three |
| **After** | OCR targets, masks of any shape, element targets, the VS Code extension, MCP, the installer, a registry | |

## 14. Also designed for from the start

### Moving over
- **Today's bots carry over:** `darbit migrate` converts a bot's pictures and settings files, `darbit.toml` and `config.toml` into `bot.toml`, and its actions and tapes to the new format. It keeps a copy of everything it changes.
- **The live bot stays untouched:** it keeps running on its pinned release (v0.3.0, then v0.4.0) until ad-bot runs a full day on the new core (milestone 2). The new darbit is a new major version, so nothing moves by accident.

### Several bots, monitors and a locked PC
- **Several bots at once,** each on its own window, account or monitor (section 5).
- **Monitors:** a bot names its monitor (or follows its window's). Display scaling is read per monitor, not once for the whole desktop.
- **A locked screen, remote desktop or a virtual machine:** screen capture and input stop working when Windows is locked or a remote session is minimised. darbit detects it, pauses the bot, says why, and goes on when the screen is back. A `doctor` check warns before a run.

### Secrets, recovery and keeping history small
- **Secrets** (a private server link, webhook tokens) live in the environment or Windows' credential store, read through `d.secret("name")`. They never sit in `bot.toml` or git.
- **Recovery policy, per bot:**
  - after a crash: restart it, up to N times an hour;
  - after a failure: go back to a known screen (the screen map), then retry;
  - after many failures in a row, or targets that stopped matching (a game update): stop and notify.
- **Retention:** run history kept N days (30 by default), screenshots M days or up to a size; cleaned by the service.

### Updates, docs and scheduling
- **Updates:** the Studio checks for a new release and offers it; channels are stable and preview. Bots move to a new darbit only when their pin moves.
- **Docs:** a getting-started guide, a sample bot (`examples/`) that's tested in CI, and an API reference made from the docstrings.
- **Scheduling in the core:** `d.schedule` with time zones (the game's UTC resets and your local clock), every N minutes, daily at a time, and windows like "the first 9 minutes of the hour", on APScheduler. The service runs schedules; a dry run shows what would run when.

### Later
- **Licenses:** PySide6 is LGPL (fine unmodified in an MIT/Apache app, to be noted), and OCR models have their own licenses.
- **Game rules:** a README note that automating a game can go against its terms.
- **Accessibility and language:** keyboard-only use, screen readers, translated text.

## 15. Decided

| Question | Decision |
|---|---|
| The Studio's screens | QML, with Python behind it |
| How the processes talk | a local socket with typed JSON messages |
| Recording input | Raw Input in its own Python worker process |
| The test bench's game screens | a private repo, pulled by CI; small made-up screens in the public repo |

## 16. Still open

- Which matching options are worth their cost, decided from the test bench's numbers.
