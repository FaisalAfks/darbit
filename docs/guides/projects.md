# Bot projects

A bot is a folder with a `darbit.toml`. When a script imports darbit, darbit looks for the nearest `darbit.toml` from the script's folder upward and applies it. A script without one runs exactly as before.

```toml
[bot]
name = "my-bot"
version = "0.4.0"
darbit = ">=0.3,<0.4"            # the darbit it needs; another version gives a warning, not an error
entry = "my_bot.main:main"       # a function, a module ("my_bot"), or a script ("bot.py")
window = "Game"                  # the app it plays: brought to the front before any input
accent = "#ff7ab6"               # its colour in Studio and on its texts
captured_at = { size = [2560, 1600], scale = 1.5 }

[settings]                       # darbit's settings for this bot
timeout = 3
similarity = 0.85
day_starts = "00:00 UTC"         # the bot's day: a game that resets at midnight UTC

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

## The bot's day

A bot's day starts at midnight on the PC's clock unless `day_starts` says otherwise: `"03:00"` (the PC's clock) or
`"00:00 UTC"` (the same moment wherever the PC is, for a game that resets at midnight UTC). The run report and log
files, history, the Studio's Overview and Results, and the daily summary all go by it, so a night that runs past
midnight stays in one day, and the Results timeline runs on past 24:00 (still read as 01:00, 02:00).

## What a bot shows in darbit Studio

Most of a bot's Overview comes from what darbit already records: the open `d.step(...)` names (Now), its top-level steps (Today's round), `d.record(...)` (What happened), failed steps with their screenshots, and `d.observe(...)` (Watching). Two calls add the rest:

```python
d.progress("Quests this week", done, 133)  # a ring; call again with new numbers
d.next("Weekly reset", reset_time)  # a datetime; shown as "in 2 d 4 h"
d.record.recovered("rejoin", "disconnected")  # counted by reason in the day's results and the Overview's Recoveries
d.show(
    "Boat", 7, sub="next upgrade at 2 000 gold"
)  # a block of the bot's own: a number, a ring (total=), a list or text


@d.block("Bait left", every=60)  # the same, asked for every minute while the bot runs
def bait():
    return state.bait  # a value, or a dict of d.show's arguments
```

Blocks of the bot's own, and its actions as buttons, show in the Overview's gallery under the bot's name. The bot's
default layout is `overview.toml` beside `darbit.toml`, read from top to bottom into rows of 12:

```toml
[[block]]
kind = "now"           # now, round, list, number, ring, chart, text, screen, button or recoveries
width = 8              # 3, 4, 6, 8 or 12

[[block]]
kind = "ring"
shows = "progress:Quests this week"   # now, round, next, failures, watching, activity, screen, recoveries,
width = 4                                 # progress:<label>, gain:<name>, block:<name>, action:<name>

[[block]]
kind = "chart"
shows = "gain:Coins"
title = "Coins this week"
width = 6
```

Without `overview.toml`, the older `[studio] tiles` order the default:


```toml
[studio]
summary = "Daily quests and shop runs, all day"
tiles = ["now", "progress:Quests this week", "next", "round", "activity", "watching"]
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
[quests]
label = "Daily quests"

  [quests.enabled]
  type = "bool"
  default = true
  help = "The next quest, every 30 minutes."

  [quests.every_minutes]
  type = "int"
  default = 30
  min = 10
  max = 120
```

Types: `bool`, `int`, `float`, `str`, `choice` (with `options`), `keys`, `target`, `region`, `location`, `list`. A missing `config.toml` is made from the defaults; a value of the wrong type or outside its limits is an error naming the key and the rule. Saving from the Studio keeps the comments in `config.toml`.

The bot reads them as one object:

```python
cfg = d.config()  # settings.toml and config.toml in the bot's folder (where its darbit.toml is)
if cfg.quests.enabled:
    every = cfg.quests.every_minutes
```

## Trying again

A step that can fail raises `d.Failed("what happened")`; `d.keep_trying` records why, gets the bot going again and
tries once more. Each try is a step in the run report; each recovery shows on the Results page:

```python
def attempt():
    if not d.click("Menu.Start"):
        raise d.Failed("no Start button")


d.keep_trying("Daily quest", attempt, recover=restart_the_game, go_on=quests_left, how="restart")
```

An observer's interrupt is handled the same way, and `recover` runs with observers muted, so closing and opening
the game doesn't trip them. `go_on` is asked before each try; when it says no, `keep_trying` returns False.

With a [screen map](screen-map.md), most failures don't need a restart. `back_to` names a screen to go back to
first:

```python
d.keep_trying("Daily quest", attempt, recover=restart_the_game, how="restart", back_to="Menu")
```

After a failure it goes back to the Menu (`d.go`, observers muted) and tries again. When that try fails too, or the
way back is lost, it calls `recover` as before. It goes back once per run of failures: a try that goes through, or a
`recover`, lets the next failure go back again. The Results page counts each go-back as "back to Menu", apart from
the restarts. `screens=` takes another `d.Map()` instead of `d.screens`.

The way back waits as long as `d.go` does for each screen (`settings.timeout`), including for finding where the
game is. When nothing on the map shows (a loading screen, the game closed), that's the whole timeout before
`recover`. `back_timeout=` waits less, so a bot that's clearly lost restarts sooner:

```python
d.keep_trying("Daily quest", attempt, recover=restart_the_game, how="restart", back_to="Menu", back_timeout=10)
```

## Tests

A bot's tests run on saved screens with `darbit.testing.FakeGame`, and with real input off so a call a test forgot
to fake raises instead of clicking the PC: `pytest_plugins = ["darbit.testing.no_real_input"]` in
`tests/conftest.py` ([Testing without the game](screen-map.md#testing-without-the-game)).

## Mistakes

An unknown table or key, a missing `[bot] name`, or a setting of the wrong type (`timeout = "long"`) stops `import darbit` with a message naming the key. A `darbit = ...` that isn't plain comparisons (`>=0.3,<0.4`) gives a warning.
