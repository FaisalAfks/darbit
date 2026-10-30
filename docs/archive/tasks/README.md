# Tasks

Every task on the roadmap, as instructions. Each page says what to build, which files, the steps, the contracts it must keep and when it's done. Rules for working on them are in [CONTRIBUTING.md](../../../CONTRIBUTING.md).

The focus is one suite: **darbit Studio** (the hub app) and its **tools** (capture, highlight, guide, recorder, run panel, flow editor) on one front end, with a fast back end behind it. Decisions behind the plan: [decisions/](../../decisions/README.md).

## Order

```
v0.2  T22 window-relative targets
v0.3  T01 ui package ─┬─ T02 tokens and themes ── T03 components ─┐
                      └─ T04 keymap ─────────────────────────────┤
      T05 local server ── T06 desktop windows ── T07 overlay test ┤
      T08 capture engine ────────────────────────────────────────┼── T09 capture overlay ── T10 capture editing
      T21 fast capture and benchmark                              ├── T11 highlight
                                                                  └── T12 setup guide ── T13 retire the Tk tool
v0.4  T14 run files (flows) ── T15 recorder ── T26 checks while recording ── T16 player and run panel
v0.5  T17 projects ── T18 settings form ── T19 new, install, run ── T20 Studio
      T27 flow editor ── T28 flow ↔ Python ── T29 custom actions
      T30 what a bot shows (before T20)
later T23 VS Code extension, T24 text targets and masks, T25 docs site and installer
```

Tasks on the same line after a `──` wait for the one before it. Tasks in different rows can be done at the same time.

## List

| Task | Milestone | Issue | Depends on |
|---|---|---|---|
| [T01 UI package and build](T01-ui-package.md) | v0.3 | #45 | |
| [T02 Design tokens, themes and motion](T02-tokens-themes.md) | v0.3 | #45 | T01 |
| [T03 Components](T03-components.md) | v0.3 | #45 | T02 |
| [T04 Keymap: every shortcut in one file](T04-keymap.md) | v0.3 | #66 | T01 |
| [T05 Local server and events](T05-local-server.md) | v0.3 | #46 | |
| [T06 Desktop windows](T06-desktop-windows.md) | v0.3 | #67 | T01, T05 |
| [T07 Freeze overlay test](T07-overlay-test.md) | v0.3 | #47 | T06 |
| [T08 Capture engine: click to select and snapping](T08-capture-engine.md) | v0.3 | #38 | |
| [T09 Capture overlay](T09-capture-overlay.md) | v0.3 | #48 | T03, T04, T07, T08 |
| [T10 Capture editing: add, undo, nudge, retake](T10-capture-editing.md) | v0.3 | #68 | T09 |
| [T11 Highlight: what's found, with scores](T11-highlight.md) | v0.3 | #69 | T03, T06 |
| [T12 Setup guide and capture from a bot](T12-setup-guide.md) | v0.3 | #70 | T09 |
| [T13 Retire the Tk capture tool](T13-retire-tk.md) | v0.3 | #71 | T09, T10, T12 |
| [T14 Run file format](T14-run-files.md) | v0.4 | #49 | |
| [T15 Recorder](T15-recorder.md) | v0.4 | #39 | T04, T06, T14 |
| [T16 Player and live run panel](T16-player-run-panel.md) | v0.4 | #40 | T03, T14 |
| [T17 Projects and layered settings](T17-projects.md) | v0.5 | #50 | |
| [T18 Settings schema and form](T18-settings-form.md) | v0.5 | #51 | T03, T17 |
| [T19 darbit new, install and run](T19-cli.md) | v0.5 | #52 | T17 |
| [T20 Studio (hub app)](T20-hub.md) | v0.5 | #53 | T03, T05, T11, T18, T19 |
| [T21 Fast capture and benchmark](T21-fast-capture.md) | v0.3 | #72 | |
| [T22 Window-relative targets](T22-window-targets.md) | v0.2 | #13 | |
| [T23 VS Code extension](T23-vscode.md) | v0.6 | #54 | T05, T03 |
| [T24 Text targets and masks](T24-text-masks.md) | v0.7 | #55, #56 | |
| [T25 Docs site, installer, API freeze](T25-v1.md) | v1.0 | #57, #58, #59 | all |
| [T26 Checks while recording](T26-checks-while-recording.md) | v0.4 | #79 | T09, T15 |
| [T27 Flow editor](T27-flow-editor.md) | v0.5 | #80 | T14, T16, T03 |
| [T28 Flow ↔ Python](T28-flow-python.md) | v0.5 | #81 | T14, T27 |
| [T29 Custom steps with `@d.action`](T29-custom-actions.md) | v0.5 | #82 | T27 |
| [T30 What a bot shows in the Studio](T30-what-a-bot-shows.md) | v0.5 | | T17 |

## How a task page is laid out

- **Goal**: one or two sentences.
- **Depends on** and **Files**: what must be merged first, and the files to fill in (placeholders already exist).
- **Steps**: in order.
- **Contracts**: names, messages and formats other tasks rely on. Don't change them without changing the other side.
- **Done when**: what has to be shown.
- **Tests**.
- **Not in this task**: so it stays small.
