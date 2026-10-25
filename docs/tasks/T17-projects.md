# T17 Projects and layered settings

**Goal:** a bot is a project folder with a manifest, and darbit's settings come in layers: defaults, then the project's `darbit.toml`, then code, then one call's arguments.

**Depends on:** nothing. **Issue:** #50. **Milestone:** v0.5. **Design:** [design.md §4–5](../design.md).

## The manifest: `darbit.toml`

```toml
[bot]
name = "ad-bot"
version = "0.2.0"
darbit = ">=0.5,<0.6"
entry = "bot.py"                 # or "ad_bot.main:main"
window = "Roblox"                # the app it plays
accent = "#ff7ab6"               # its colour in the hub and on its texts (T12)
captured_at = { size = [2560, 1600], scale = 1.5 }

[settings]                       # darbit's own settings for this bot (layer 2)
timeout = 3
similarity = 0.85

[images]
folders = ["images"]

[keys]                           # keymap overrides (T04)
"run.stop" = "ctrl+alt+x"
```

## Files

- `packages/darbit/src/darbit/project/manifest.py`: `Project`, `find(path)` (walks up to the nearest `darbit.toml`), `load()`
- `packages/darbit/src/darbit/settings.py`: apply layer 2 when a project is found at start
- `packages/darbit/tests/test_project.py`

## Steps

1. `find()` from the script's folder upward; none found = today's behaviour exactly.
2. Layering: `settings` reads defaults, then `[settings]`, then whatever code sets, and calls keep overriding per call (they already do). Log where each non-default value came from once at start.
3. `[images].folders` are added to the image search path (`settings.images`).
4. Version check: warn (don't fail) when the installed darbit doesn't match `darbit = ...`.
5. ad-bot gets a `darbit.toml` in its own repo (separate PR there).

## Done when

ad-bot runs with a `darbit.toml` and its settings come from it; a script without one runs as before.

## Tests

`find`, layering order, image folders, version warning.
