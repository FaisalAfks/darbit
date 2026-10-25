# Observers and saved state

Watching for something in the background, and values that survive restarts.

## Observers

Watch for something in the background, and interrupt the script when it shows up:

```python
d.observe("Roblox.Disconnected")                                    # an image
def roblox_closed():
    return not d.apps.running("Roblox")

d.observe(roblox_closed, name="Roblox closed")                      # a condition

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
if s.weekly(weekday=0, hour_utc=7):   # True once each week, from Monday 07:00 UTC
    s["done"] = 0
s.count("done")                       # add 1, saved at once
raid = s.timer("speed raid", minutes=30)
if raid.due():
    ...
    raid.restart()
```

`s.daily(hour_utc=0)` works like `weekly` for days. Every change is written straight away, so a crash or the stop hotkey loses nothing.
