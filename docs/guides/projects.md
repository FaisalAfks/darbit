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

## Modes and steps

A bot that runs a round of modes can say which, so darbit Studio can run one of them, or one step of one, on its
own: to test a fix without the whole round (decision 0022). Each mode is the name of a top-level `d.step`, with the
names of the steps inside it:

```toml
[modes]
"Daily quest" = ["pick a quest", "claim it"]
Shop = []
```

The Studio's Today's round and its command palette (Ctrl+K) then offer **Run only Daily quest** and **Run step:
Daily quest · claim it**; the CLI has `darbit start my-bot --only "Daily quest" --step "claim it"`. The bot honours it
with `d.wants` and ends after one pass when `d.only()` says it was started for one:

```python
def main():
    while True:
        for mode in ["Daily quest", "Shop"]:
            if d.wants(mode):
                with d.step(mode):
                    run(mode)
        if d.only():
            return  # one mode or step: done
        d.sleep(60)


def daily_quest():
    if d.wants("Daily quest", "pick a quest"):
        with d.step("pick a quest"):
            ...
    if d.wants("Daily quest", "claim it"):
        with d.step("claim it"):
            ...
```

`d.wants(mode)` is always true in a round. Started for a mode, it's true for that mode and every step of it; for a
step, for that mode and that step only. A step that needs an earlier one's work (a list open) does that itself, or
the bot checks for it. `d.plan` keeps only the mode asked for. darbit doesn't skip anything on its own: a bot that
declares modes honours them. `[modes]` needs a darbit that knows it: an older one refuses the darbit.toml.

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
kind = "now"           # now, round, list, number, ring, chart, text, screen, sees, button or recoveries
width = 8              # 3, 4, 6, 8 or 12

[[block]]
kind = "ring"
shows = "progress:Quests this week"   # now, round, next, failures, watching, activity, screen, sees, recoveries,
width = 4                                 # progress:<label>, gain:<name>, block:<name>, action:<name>

[[block]]
kind = "sees"          # What the bot sees: its last look, with what it looked for boxed
title = "What the bot sees"
width = 8

[[block]]
kind = "chart"
shows = "gain:Coins"
title = "Coins this week"
width = 6
```

`sees` shows the screen at the bot's last look (`exists`, `wait`, `vanish`) with what it looked for boxed: found
ones solid with their name and score, the others dashed at their closest spot. It costs the bot a small picture a
second (made on a thread of its own, about 10 ms, plus one more grab when the look searched only part of the screen),
and only while the block is in sight in darbit Studio; otherwise nothing. It's never in darbit's own default layout:
place it here, or add it in Customize.

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
input = true    # the bot uses the mouse and keys (the default); false for one that only watches or reads
```

Bots on one desktop share one mouse and keyboard, so the service runs one bot with `input = true` at a time; a bot
with `input = false` runs alongside anything. See [the service](service.md#one-bot-that-sends-input-at-a-time). Each
`[run]` key is checked, so a bot that sets `input` needs a darbit newer than 1.0.0-alpha.6.

How long a bot's run reports, daily logs and history are kept is the `keep_days` setting, in `[settings]`:

```toml
[settings]
keep_days = 14  # days kept before today (14 by default); older ones are deleted, today's and yesterday's never
```

The bot deletes its own old reports and logs when it starts writing and as each new day starts. The service deletes
the history (and the files of a bot on an older darbit) when it starts, when it starts a bot, and every six hours.
Days go by the bot's `day_starts`. Screenshots keep the newest few hundred whatever their age. An older darbit.toml
with `keep_days` in `[run]` still works; a bot that sets it in `[settings]` needs a darbit newer than 1.0.0-alpha.7. See
[decision 0021](../decisions/0021-keeping-history-small.md).

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
