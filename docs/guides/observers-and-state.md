# Observers and saved state

Watching for something in the background, and values that survive restarts.

## Observers

Watch for something in the background, and interrupt the script when it shows up:

```python
d.observe("Roblox.Disconnected")  # an image


def roblox_closed():
    return not d.apps.running("Roblox")


d.observe(roblox_closed, name="Roblox closed")  # a condition

try:
    play()
except d.Interrupted as event:
    d.log(f"{event.name}: rejoining")
    with d.no_interrupts():
        rejoin()
```

When an observer fires, held keys are let go and the next darbit call (a wait, a click, a sleep) raises `Interrupted` once. It fires again only after what it watches has gone away and come back. All image observers share one screen capture every half second. `observer.stop()` or `d.stop_observing()` ends them.

## Saved state

Values that survive restarts, kept in `.darbit/state/` next to the script:

```python
s = d.State("speedraid")
if s.weekly(weekday=0, hour_utc=7):  # True once each week, from Monday 07:00 UTC
    s["done"] = 0
s.count("done")  # add 1, saved at once
raid = s.timer("speed raid", minutes=30)
if raid.due():
    ...
    raid.restart()
```

`s.daily(hour_utc=0)` works like `weekly` for days. Every change is written straight away, so a crash or the stop hotkey loses nothing.

## Sharing the PC with a bot

Windows has one mouse and one keyboard, so a bot and a person can't both use them. With polite mode on, a bot steps
back when you do: it lets go of its keys and waits at its next darbit call, then goes on after a few seconds without
your mouse or keys. darbit's own clicks and keys don't count.

```toml
[settings]
polite = 5   # seconds without your mouse or keys before the bot goes on; 0 (the default) is off
```

When Windows is locked (or shows its sign-in or a UAC prompt), nothing a bot sees or presses reaches the game. A bot
notices at its next darbit call (it looks once a second), lets go of its keys, writes `screen: locked` in its run
report and waits; when the screen is back it writes `screen: back` and goes on where it was. darbit Studio's Overview
says it's waiting, and since when. The stop hotkey and the Studio's Stop still work while it waits.

With darbit Studio open, its **ghost cursor** shows where a bot clicks (a ripple) and the keys it presses (keycaps by
the cursor) over the game, for a moment each, so you can tell the bot's input from your own. Clicks go through it. It's
on by default; turn it off in darbit settings. A bot sends each one as a small message to the Studio and never waits
for it: without a Studio, nothing is sent.
