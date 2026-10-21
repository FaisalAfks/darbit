# T23 VS Code extension

**Goal:** write, capture, record and run a bot from VS Code, using the same UI components as the hub.

**Depends on:** T03, T05 (and the tools it shows: T09, T11, T16). **Issue:** #54. **Milestone:** v0.6. **Repo:** `darbit-vscode`.

## Outline

1. Connect to the local server from `%LOCALAPPDATA%\darbit\server.json` (T05); start `darbit app --headless` when none is running.
2. **Hover and margin previews** of target names in Python strings (`d.click("Gui.Play")`): the image, its size and last score.
3. **Go to definition** on a target name opens its `.png` and `.json`.
4. **Diagnostics:** names with no file; run files that fail the schema (T14).
5. **Commands:** Capture target here (opens the overlay, inserts the name), Record a run, Highlight, Run bot, Stop. Keys from the same keymap (T04) where VS Code allows.
6. **Webviews** for the run panel (T16), the library (T20 Library) and the guide progress, built from the `ui/` package with the VS Code theme mapped onto darbit's tokens.

## Done when

A bot is written, captured, recorded and run without leaving VS Code.
