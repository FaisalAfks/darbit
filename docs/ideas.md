# Ideas

Ideas for darbit, kept here until they become issues (or, once the repo is public, Discussions). Moved from the old `IDEAS.md` on 2026-10-25; the bot's ideas are in ad-bot's `docs/ideas.md`.

## Ideas so far

### Finding things on screen

| Idea | Status | Source |
|---|---|---|
| Every image carries its own search area (its region), with a whole-screen failsafe as a setting | done in landmark | Chat 2026-09-18 |
| Targets that move (a slider), appear anywhere in an area (cards in a bag grid), or live in a 3D world (read the HUD instead) | partly done | Chat 2026-09-18 |
| Images, spots and areas as one kind of thing: a named target | done in landmark | Chat 2026-09-18 |
| Similarity and click offset per target (default: the centre) | done in landmark | Chat 2026-09-18 |
| Masks: parts of an image to ignore | done in landmark (rectangles) | Chat 2026-09-18 |
| Masks and images in any shape, not only rectangles | idea | Chat 2026-09-19 |
| Text targets: capture text instead of, or as well as, an image (OCR) | done in landmark | Chat 2026-09-19, Darbit 2025 |
| Targets know their source: a window, a browser page, anything | done in landmark | Chat 2026-10-02 |
| Element targets: find buttons through the app's own UI tree, or a parser that finds what's clickable | done in landmark (UI tree) | Chat 2026-10-02 |
| Web pages by CSS selector (Playwright) | tried | Darbit 2025 |
| Find by image, text or selector with one `find` | tried | Darbit 2025 |

### Input

| Idea | Status | Source |
|---|---|---|
| Gliding mouse like SikuliX (Roblox needs it) | done in landmark | Chat 2026-09-14 |
| Keys that work on any keyboard language: game keys by position, text as text | done in landmark | Chat 2026-09-19 |
| Touch and controller input | idea | Chat 2026-09-19 |
| Hotkeys while a bot runs: one to stop it, others to trigger actions | tried | JavaSwing |

### Watching the screen

| Idea | Status | Source |
|---|---|---|
| Observers: react when something appears, vanishes or changes, instead of checking in loops | tried (SikuliX `onAppear`, oculix-rust) | Events.py, oculix-rust, Chat 2026-09-14 |
| Errors (disconnect, teleport failed) caught by a watcher instead of checked everywhere | tried | Test1 `gameFailed(event)` |

### Capture studio

| Idea | Status | Source |
|---|---|---|
| Own capture tool, since SikuliX's screenshots change the image | done in landmark | Chat 2026-09-14 |
| Select a region on screen, highlight it, save it | tried | Java `Test.java` |
| Zoom in, edit the selection instead of reselecting | done in landmark | Chat 2026-09-18 |
| Capture modes: image, spot, area; all in one view: image in green, its region in red, masks in blue, the click point as a movable cross | done in landmark | Chat 2026-09-18 |
| Exact number fields to see changes right away | done in landmark | Chat 2026-09-18 |
| Snap to corners of a shape, or to guide lines | idea | Chat 2026-10-18 |
| Grid harvest: scroll any grid menu (bag, Speed Raid list, rewards) and save every cell as its own image, using the grid's corners | idea, after parity; speeds up image taking | Chat 2026-10-19 |
| Name harvested characters from the bag's side panel (click the card, read the name), so names survive order and icon changes | idea | Chat 2026-10-19 |
| One icon per character, reused everywhere: Speed Raid list, assists, Raid Challenge and Limited Raid bonus characters | idea | Chat 2026-10-19 |
| Nothing drawn over the screenshot: pick first, then edit in a normal window | idea (decided) | Chat 2026-09-19 |
| A hotkey to check every captured image, inside and outside its region, to know if the whole-screen fallback is risky | done in landmark (`check`) | Chat 2026-09-18 |

### Writing automations

| Idea | Status | Source |
|---|---|---|
| Plain scripts in an easy language (Python) | done | Old, Chat 2026-10-19 |
| Bots in any language | idea | Chat 2026-10-19 |
| YAML flows with steps, variables, if and loops, flows inside flows with inputs | tried | Darbit 2025 |
| Recorder: record mouse and keyboard into a flow | tried | Darbit 2025 |
| Visual flow editor (desktop GUI) | tried | Darbit 2025, JavaSwing |
| Plugins: HTTP calls, files | tried | Darbit 2025 |

### AI

| Idea | Status | Source |
|---|---|---|
| MCP server so an AI agent can use the tool | tried | Darbit 2025 |
| An agent records its steps through the tool once, then the flow replays with logs and feedback, without the AI looking at every screen | idea | Chat 2026-10-02 |
| Great fit for AI computer use | idea | Chat 2026-09-19 |

### Around the tool

| Idea | Status | Source |
|---|---|---|
| A project structure, a linter and a capture tool shipped together | partly done in landmark | Chat 2026-09-18 |
| A nice desktop app to configure the bot (not like the SikuliX IDE) | idea | Chat 2026-09-14 |
| Phone control and live view | idea | Chat 2026-09-14 |
| VS Code / Antigravity extension: images shown on hover in the code | idea | Chat 2026-10-18 |
| One executable / CLI | idea | Chat 2026-10-19 |
| Rust for compile-time safety; a Rust SikuliX engine | tried | oculix-rust, Chat 2026-10-19 |
| Cross-platform: desktop, web, mobile | idea | Darbit 2025 |
| Public, MIT or Apache-2.0, open to contributions | decided | Chat 2026-10-18 |
| Paid or dual-licence version | idea | Darbit 2025 plan |
| Tool name configurable | done | Chat 2026-10-18 |

---

## Suggested later

7. **A small "doctor" command.** Checks the Roblox window size, display scale, missing targets and settings before a run, so problems show up before you're away from the PC.
8. **Failure screenshots with the target drawn on them.** When a step fails, save the screen with where the target was expected and its best score.
9. **Replays as tests.** Saved frames of each game screen, so a code change can be checked without starting the game. (landmark had a start on this.)
10. **Keep the tool small until the bot is done.** A feature goes into the tool only when the bot needs it; everything else lands here first.

## Process

11. **One folder, a few repos, one board.** The bot and the tool tracked on one GitHub project board, with each idea from this file becoming an issue only once it's chosen.
12. **One working mode at a time.** Each mode gets moved over from the old script only when the new version has run a full day; until then the old script keeps running that part.

---

## Later (from the 2026-10-20 review)

- Wait until a match stops moving before clicking (menus mid-animation)
- Pause when the mouse is moved by hand while a script runs
- Clear error when the game runs as admin and input is blocked
- Masks: parts of an image ignored when matching
- Phone notifications for the bot: errors and the daily summary (Discord webhook, ntfy or Telegram)
