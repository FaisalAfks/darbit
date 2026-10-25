# darbit design

What darbit is, what it handles, how its parts fit together, and the standards every part follows. When a decision changes, this file changes with it. The order of work is in [roadmap.md](roadmap.md).

## 1. What darbit is

A simple GUI-automation toolkit for Windows, in Python. It does what SikuliX does (find things on screen, click, type, wait) with:

- input that games accept: a gliding mouse, keys sent by position
- targets that carry their own settings
- tools to capture, record and check targets
- a way to package and share bots

People write bots as Python scripts. Recordings and run files let people who don't code build parts of a bot, like a scripted run through a level.

### Principles

1. As simple as SikuliX for a first script: `d.click("Play")`.
2. Not finding something is a value (`None` or `False`), never an exception. Exceptions are for mistakes and for stopping.
3. Every action can be confirmed on screen.
4. Targets carry their own knowledge (search area, similarity, click point, the scale they were captured at), so scripts stay short.
5. darbit handles the machinery; the bot author handles the logic of their app or game (section 3).
6. One look and feel across every window, the hub app and the IDE extension (section 9).
7. Everything is observable: a log, screenshots of failures, a run report.
8. Fast by default (section 12).

## 2. Package layout

The Python package `darbit`, in layers that only depend on the layers below them:

| Layer | Holds |
|---|---|
| `core` | geometry, targets, matching, the run-file model; no screen, so it's fully testable |
| `platform` | screen capture, input, windows, display scaling, the stop hotkey; Windows now, others later |
| `runtime` | find, act and wait; observers and interrupts; the state store; logging; the run report |
| `project` | `darbit.toml`, settings layers, the bot manifest, the settings schema, the target library |
| `tools` | capture, highlight, setup guides, record, play (run files), check (library health) |
| `server` | a local API (FastAPI and WebSocket) for the UI, the IDE extension and later MCP |
| `ui` | the web front end, a TypeScript package in `ui/`, built into the Python wheel |
| `cli` | `darbit new`, `capture`, `record`, `play`, `check`, `run`, `install`, `app` |

Repositories:

- `darbit`: the package, the UI, the docs
- `darbit-vscode`: the IDE extension, using the same UI package
- each bot in its own repository

## 3. What darbit handles and what the bot author handles

| darbit | The bot author |
|---|---|
| Finding, input, waits, timeouts | What to look for, and in what order |
| Targets: files, scale, search areas, checks | Capturing the targets for their app |
| Observers: watching for events and interrupting the script | What to do when one fires, e.g. rejoin |
| A state store: saved values, counters, daily and weekly resets | What to save |
| Timers and clock helpers | Schedules and modes |
| Recording, playing and editing run files | Recording their runs |
| Logs, screenshots, the run report | Reading them |
| Bot settings: schema, generated form, loading | Declaring which settings their bot has |
| Packaging, installing and running a bot | Publishing the repository |

darbit ships nothing specific to one app or game, and no scheduler of modes.

## 4. Settings

Layers, the last one wins:

1. **darbit's defaults:** timeout, similarity, mouse glide, scan rate, stop key, logs.
2. **The project's `darbit.toml`:** the same keys, saved per project, plus `[windows]` (named app windows) and `[images]` (image folders).
3. **Code:** `d.settings.timeout = 10`, as in SikuliX.
4. **One call:** `d.click("Play", timeout=5)`.

A bot's own settings (modes, attempts, team, ...) are declared in its `settings.toml`, with a type, a default, a label and help text for each. darbit loads the user's values from `config.toml` and checks them against the schema. The hub app and the IDE extension show a form generated from the schema, so users don't edit files by hand.

## 5. Bot projects and sharing

```
my-bot/
  darbit.toml        name, version, darbit version needed, app window, screen size and scale captured at
  settings.toml      the bot's settings schema
  config.toml        the user's values; git-ignored, created from the schema's defaults
  bot.py             entry point
  images/            targets: .png and .json
  runs/              recorded run files: .yaml
  guide.toml         the setup guide: what to capture, screen by screen, in order
  state/  logs/      created when the bot runs; git-ignored
```

- `darbit new` creates a project, `darbit install <git url>` installs one, `darbit run` starts it.
- **Other screens:** targets record the screen size and scale they were captured at. darbit rescales them (section 6), and `darbit check` lists the targets that need recapturing on this screen.
- A registry of bots can come later, on top of this format.

## 6. Targets

- **Kinds:** image, location and region now; text (read with OCR) and masks later; UI elements after that.
- **Storage:** a `.png` and a `.json` with the search area, similarity, click offset, and the scale and window size the target was captured at.
- **Following the window:** positions are relative to the app's window, and images are rescaled by the change in scale and window size, with a multi-scale search as a fallback.
- **Library health:** `darbit check` scores every target inside its search area and everywhere else, and gives each one a verdict: ok, risky, missing or moved. Scores are kept over time, and saved screenshots can be checked again after a target is recaptured.

## 7. Runtime

- `exists`, `wait`, `vanish`, `find_all`, the mouse and keyboard calls, apps and settings, as in v0.1.
- **Observers:** `d.observe("Disconnected")`, or a condition such as "the window closed". They run on a background thread and only report. The next darbit call in the script raises `Interrupted(event)`, and the script decides what to do. All observers share one screen capture per tick.
- **State store:** `d.State("speedraid")` for saved values, counters, daily and weekly resets, and timers.
- **Run report:** each run records its steps, outcomes, durations, match scores and screenshots. It feeds `darbit check` and the hub's history.
- Kept from v0.1: the stop hotkey, keeping the PC awake, the window-in-front guard, letting go of held keys on exit.

## 8. Recordings and run files

A run file is YAML, with a JSON Schema so editors check and complete it:

```yaml
run: Slime
checkpoints:
  - name: Wave 1
    wait_for: Dim.Game.Left          # must be on screen before this part starts
    goals:
      - name: Clear the left side
        steps: [hold: w, wait: 0.5, press: q, do: dodge, turn: -90]
actions:                             # reusable steps, like functions
  dodge: [press: space, wait: 0.3, press: space]
```

- **`darbit record NAME`** records keys, clicks and camera turns (right-drag and arrow keys) with their timings. While recording:
  - **Ctrl+Alt+M** marks a checkpoint; click to select takes the image it waits for
  - **Ctrl+Alt+P** pauses and resumes
  - **Ctrl+Alt+R** stops (it also starts)
- **`d.play("runs/slime.yaml")`** plays it from a script; `darbit play` plays it on its own. Each checkpoint confirms the app is where it should be before going on.
- **The live run panel** is docked to the side of the screen and never takes focus from the app. It shows checkpoints, goals and steps, with the current one highlighted. From it:
  - set breakpoints
  - pause and step
  - edit a wait
  - insert a step or a camera turn
  - save the changes back to the file

## 9. One UI system

Every window, the hub app and the IDE extension are built from one web UI package.

- **Design tokens** in one file: colours, type scale (Segoe UI and the system font), spacing, corner radius, motion. Themes: glass dark (default), glass light, midnight, high contrast, and custom themes from a file. Details in [ui/design-system.md](style/ui/design-system.md).
- **Text slots:** text on any surface is darbit's (`tool`), a bot's (`bot`) or a setup guide author's (`guide`), each styled differently.
- **Keys:** every shortcut is in one remappable file and every shortcut is also a button ([ui/keymap.md](style/ui/keymap.md)).
- **Components:**
  - card
  - pill button
  - keycap
  - toast
  - list and tree
  - form fields, generated from a settings schema
  - image thumbnail with a score badge
  - freeze overlay with its toolbar
  - magnifier
  - progress strip
- **Stack:** TypeScript and Svelte 5, with Konva for canvas editors. Desktop windows run in pywebview (WebView2); the IDE extension uses VS Code webviews. Both talk to darbit's local server.
- **Windows built from it:**
  - the capture overlay
  - highlight, over the screen and click-through
  - the setup guide card, which hides at the top of the screen
  - the recorder bar
  - the live run panel
  - the library and check report
  - the hub app: projects, a bot's settings form, start and stop, the live view, logs and run history
- **The freeze overlay** moves to the web UI as well. A short test first checks that a full-screen pywebview window shows a 2560×1600 screenshot smoothly. If it doesn't, that one overlay stays native, styled with the same tokens.

Mockups of the main windows are in [ui/mockups.html](ui/mockups.html). Each part has its own task in [tasks/](tasks/README.md).

## 10. The IDE extension (VS Code)

What it adds over a plain editor:

- image previews when hovering over a target name, and in the margin
- going to a target's image and its `.json`
- errors for missing targets and invalid run files
- commands such as "Capture target here" and "Record a run", which insert the result at the cursor
- running and stopping the bot, with its log, screenshots and the live run panel inside VS Code
- a visual editor for run files, and a target library view with health scores

It uses the same UI components as the hub app.

## 11. MCP (after v1)

An MCP server lets AI agents use a project's captured targets by name (`find`, `click`, `wait`, `check`) instead of guessing coordinates, and record runs. The local server is built so MCP can be added as a thin layer on it.

## 12. Speed

- **Implemented:**
  - each target is searched only inside its own area
  - target images are cached
- **Planned:**
  - one screen capture for several targets, and for all observers per tick
  - a faster capture back end (Windows Graphics Capture or DXGI) behind the same interface
  - optional greyscale or downscaled matching for large areas
  - multi-scale matching only as a fallback
  - a scan rate that adapts
- **A benchmark suite** (match time, capture time, CPU use while waiting) runs in CI, so speed doesn't regress.

## 13. Quality and releases

- **Tests at three levels:**
  - offline, with fakes and saved screenshots
  - replays of saved app screens
  - an opt-in live suite against darbit's own test window
- **CI on Windows:** lint, tests, the benchmark.
- **Releases:** SemVer, a changelog, GitHub releases. The public API is stable from v1.0; anything removed is announced one minor version before.
- **Docs:** a site with getting started, the API, the tools, the bot project format, and a guide to writing a bot.
