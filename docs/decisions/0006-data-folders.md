# 0006 Where darbit keeps its files: AppData and a project's `.darbit/`

Accepted, 2026-10-25.

## Context

Runtime files landed in the project folder: `state.json` and `logs/` (671 MB of screenshots in ad-bot). Settings paths were picked one by one in different modules. darbit is meant to become a standalone Studio as well as a library, so it needs one agreed place for each kind of file.

## Decision

One module, `darbit/paths.py` (using `platformdirs`), gives every path:

| What | Where |
|---|---|
| user settings, keymap, themes | `%APPDATA%\darbit\` |
| app data: installed bots, `server.json`, Studio state | `%LOCALAPPDATA%\darbit\` |
| cache: thumbnails, prepared frames | `%LOCALAPPDATA%\darbit\Cache\` (safe to delete) |
| app logs: Studio, server | `%LOCALAPPDATA%\darbit\Logs\` |
| a project's runtime files: state, logs, run history, cache | `<project>\.darbit\` (git-ignored, like `.venv`) |

- Installed bots live in `%LOCALAPPDATA%\darbit\bots\<name>\` (ADR 0001).
- Screenshots are saved as JPEG (quality 85), about 10 times smaller than PNG.

## Consequences

- `settings.logs`, `settings.state` and ad-bot's `state.json` move into `.darbit/`; existing files are copied over once.
- Cleaning a machine means deleting known folders.
