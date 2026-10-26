# Bot projects

A bot is a folder with a `darbit.toml`. When a script imports darbit, darbit looks for the nearest `darbit.toml` from the script's folder upward and applies it. A script without one runs exactly as before.

```toml
[bot]
name = "ad-bot"
version = "0.4.0"
darbit = ">=0.3,<0.4"            # the darbit it needs; another version gives a warning, not an error
entry = "ad_bot.main:main"       # a function, a module ("ad_bot"), or a script ("bot.py")
window = "Roblox"                # the app it plays: brought to the front before any input
accent = "#ff7ab6"               # its colour in Studio and on its texts
captured_at = { size = [2560, 1600], scale = 1.5 }

[settings]                       # darbit's settings for this bot
timeout = 3
similarity = 0.85

[images]
folders = ["assets/images"]      # searched first, relative to the project

[keys]                           # keymap overrides (later, with the keymap)
"run.stop" = "ctrl+alt+x"
```

## Settings come in layers

The last one wins:

1. darbit's defaults
2. the project's `[settings]`
3. what the script sets: `d.settings.timeout = 10`
4. one call's own argument: `d.click("Play", timeout=5)`

`[settings]` takes every setting in `d.settings` except `images`, which come from `[images]`. `logs` and `state` are folders relative to the project, and default to its `.darbit/logs` and `.darbit/state`. The day's log starts with the values the manifest set.

## Mistakes

An unknown table or key, a missing `[bot] name`, or a setting of the wrong type (`timeout = "long"`) stops `import darbit` with a message naming the key. A `darbit = ...` that isn't plain comparisons (`>=0.3,<0.4`) gives a warning.
