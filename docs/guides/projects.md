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

## What a bot shows in darbit Studio

Most of a bot's Overview comes from what darbit already records: the open `d.step(...)` names (Now), its top-level steps (Today's round), `d.record(...)` (What happened), failed steps with their screenshots, and `d.observe(...)` (Watching). Two calls add the rest:

```python
d.progress("Speed Raid this week", done, 133)  # a ring; call again with new numbers
d.next("Weekly reset", reset_time)  # a datetime; shown as "in 2 d 4 h"
```

`[studio]` picks and orders the tiles (decision 0011):

```toml
[studio]
summary = "Raids, Speed Raid, challenges and AFK, all day"
tiles = ["now", "progress:Speed Raid this week", "next", "round", "activity", "watching"]
```

Tiles: `now`, `round`, `progress` (or `progress:<label>` for one), `next`, `activity`, `failures`, `watching`, `setup`. Without the table, all of them in that order; a tile with nothing to show is left out.

`[run]` is how darbit's service runs the bot. `restart` starts it again a few seconds after it fails (ends with an
error, not a Stop), up to that many times an hour; after that it's left stopped. A phone notification (`notify.toml`)
says which:

```toml
[run]
restart = 3     # 0 (the default) leaves a failed bot stopped
keep_days = 30  # days of run history, run reports and daily logs kept (30 by default); older ones are deleted
```

The service tidies when it starts and every six hours. Screenshots keep the newest few hundred whatever their age.

For a failure the bot can get past itself, go back to a known screen and try again in its own code (`d.go`, see the
screen map guide); `restart` is for when the bot itself ended.

## The bot's own settings: settings.toml

A bot declares its settings once; the Studio shows a form for them and `config.toml` holds the values:

```toml
[speed_raid]
label = "Speed Raid"

  [speed_raid.enabled]
  type = "bool"
  default = true
  help = "The next character, every 30 minutes."

  [speed_raid.every_minutes]
  type = "int"
  default = 30
  min = 10
  max = 120
```

Types: `bool`, `int`, `float`, `str`, `choice` (with `options`), `keys`, `target`, `region`, `location`, `list`. A missing `config.toml` is made from the defaults; a value of the wrong type or outside its limits is an error naming the key and the rule. Saving from the Studio keeps the comments in `config.toml`.

## Mistakes

An unknown table or key, a missing `[bot] name`, or a setting of the wrong type (`timeout = "long"`) stops `import darbit` with a message naming the key. A `darbit = ...` that isn't plain comparisons (`>=0.3,<0.4`) gives a warning.
