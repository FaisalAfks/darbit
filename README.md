# darbit

Simple GUI automation for Windows, in Python. Find images on the screen, click, type and wait, the way SikuliX does it, with input that games like Roblox accept.

```python
import darbit as d

d.settings.timeout = 10

if d.click("Gui.Play"):                         # waits up to 10 s, False if it never shows
    d.wait("Play.Raid", "Roblox.Disconnected")  # the first of several
    d.press("tab")
    d.press(*"54132")                           # game keys, one after another

if m := d.exists("Dim.Game.Left", 90):          # a Match, or None
    d.hold("w")
    d.sleep(2)
    d.release()
```

Not finding something is a normal result: `None` or `False`, never an error.

## Install

```
pip install git+https://github.com/FaisalAfks/darbit
```

Python 3.11 or newer, Windows.

## Targets

A target is a name like `Gui.Play` or `lobby/play`. It's looked up in the `images` folder next to the script (and the script's own folder): `Gui.Play.png`, plus an optional `Gui.Play.json` with its settings:

```json
{"region": [2133, 404, 428, 1125], "similarity": 0.85, "offset": [0, 12]}
```

- `region`: where to search; without it the whole screen
- `similarity`: lowest score that counts as found, 0 to 1 (default `settings.similarity`)
- `offset`: click point from the image's centre
- `location`: a fixed point, for targets without an image

A target can also be made in code: `d.Target("Bag.Character.png", similarity=0.6)`.

All positions are real screen pixels, also on scaled displays (150% etc.).

## Calls

| Call | Does | Returns |
|---|---|---|
| `exists(target, timeout=0, region=None)` | looks for a target, up to `timeout` seconds | `Match` or `None` |
| `wait(*targets, timeout=None, region=None)` | waits for a target, or the first of several (`match.name` says which) | `Match` or `None` |
| `vanish(target, timeout=None)` | waits until the target is gone | `True` / `False` |
| `find_all(target)` | every place the target is | list of `Match` |
| `check(*targets)` | names of targets whose image file is missing | list |
| `click`, `double_click`, `right_click`, `hover` | on a target, a `Match` or a `Location`; waits up to `settings.timeout` for a target | `True` / `False` |
| `drag(target, to=...)` | drag and drop, like SikuliX's `dragDrop` | `True` / `False` |
| `scroll(notches, at=None)` | mouse wheel; positive scrolls up | `True` / `False` |
| `press("tab")`, `press("ctrl+a")`, `press(*"54132")` | presses and lets go of each key in order | |
| `hold("w")`, `release("w")`, `release()` | keeps keys down; `release()` lets go of everything | |
| `write("hello")` | types text in any keyboard language | |
| `sleep(seconds)` | waits, but stops at once on the stop hotkey | |
| `apps.open(path_or_url)`, `apps.close(app)`, `apps.running(app)`, `apps.focus(app)`, `apps.window(app)` | an app by window title (`"Roblox"`) or program (`"chrome.exe"`) | |
| `log(text)`, `screenshot(label)` | a line or a screenshot in today's log | |

`Region(x, y, w, h)`, `Location(x, y)` and `Screen()` (the whole screen) are there for `region=` and fixed points.

Keys are sent by their position on the keyboard, so games get them and the keyboard language doesn't matter. The mouse glides to each spot, which some games need to register a click.

## Settings

```python
d.settings.timeout = 3           # how long actions wait for a target
d.settings.similarity = 0.7      # default similarity
d.settings.glide = 0.5           # seconds the mouse takes to move
d.settings.scan_rate = 5         # searches per second while waiting
d.settings.window = "Roblox"     # bring this window to the front before any input
d.settings.missing_images = "skip"  # treat a missing image file as never found, instead of an error
d.settings.screenshot_after = 20 # save a screenshot when a wait this long runs out
d.stop_key("ctrl+alt+q")         # the stop hotkey
```

## Stopping

Ctrl+Alt+Q stops a running script: every held key and button is let go and the next darbit call raises `Stopped`, even in the middle of a wait or a sleep. Held keys are also let go when a script ends or crashes. While a script runs, the PC doesn't go to sleep.

## Observers

Watch for something in the background, and interrupt the script when it shows up:

```python
d.observe("Roblox.Disconnected")                                    # an image
d.observe(lambda: not d.apps.running("Roblox"), name="Roblox closed")  # a condition

try:
    play()
except d.Interrupted as event:
    d.log(f"{event.name}: rejoining")
    with d.no_interrupts():
        rejoin()
```

When an observer fires, held keys are let go and the next darbit call (a wait, a click, a sleep) raises `Interrupted` once. It fires again only after what it watches has gone away and come back. All image observers share one screen capture every half second. `observer.stop()` or `d.stop_observing()` ends them.

## Saved state

Values that survive restarts, kept in `state/` next to the script:

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

## Logs

Each day gets a log file in `logs/` next to the script: what was looked for, found, clicked and pressed. A wait of 20 seconds or more that runs out also saves a screenshot in `logs/screenshots/`.

## Run report

Next to each day's log, `logs/report-<day>.jsonl` records every search (with the closest score when nothing was found), click and drag, and the script's own steps and events:

```python
with d.step("Speed Raid"):                          # timed; ends ok, failed (with a screenshot), interrupted or stopped
    ...
    d.record("speed raid done", character="Naruto")  # an event of the script's own
```

```
python -m darbit.tools.report                       # today's summary
python -m darbit.tools.report 2026-10-21 --logs ../my-bot/logs
```

The summary shows each step's runs, failures and times, why steps ended early, the targets most often not found with their closest score, and the script's events counted by name.

## Checking a library

```
python -m darbit.tools.check --screens shots/ --similarity 0.85
```

Scores every target in `images/` against the live screen, or against saved screenshots (one per app screen works best). Each target gets a verdict:

- **ok**: found in its region, nothing else on screen comes close
- **risky**: found, but something else scores almost as high and could be clicked by mistake
- **moved**: only found outside its region, so the region needs updating
- **not seen**: not on any screen checked

Results are added to `state/check.jsonl`, to follow scores over time.

## Capture tool

```
python -m darbit.capture Gui.Play                 # one image: the screen freezes after 3 s, box it, Enter
python -m darbit.capture afk/spot --location      # a point
python -m darbit.capture --list capture.txt       # a session through a list of targets
```

A list file has one target per line, a description after `#`, grouped by the screen they're on:

```
[Lobby]
Gui.Play                 # lobby: the Play button
location: afk/spot       # where to click to stay active
region: menus/bag        # the bag window
```

In a session, a card at the top of the screen shows the next target. Open its screen and press F8: the screen freezes and every target on that screen is taken from the same shot.

- Click a button to box it, or drag a box; edges snap to lines nearby (hold Alt to stop)
- R then drag sets the search region, C then click sets the click point
- Arrows move the box by a pixel, Shift+arrows resize it
- Enter saves and goes to the next target; the image is checked on the live screen right away
- Space takes a new shot, Tab skips, Backspace undoes, Esc goes back to the card
- On the card: `+ Add` adds a target to the session and the list; Done (or Ctrl+Alt+Q) keeps or deletes the session's captures

A long scrolling list, like a character list, can be taken in one pass:

```
python -m darbit.capture --list capture.txt --harvest "Speed Raid characters"
```

Box the first cell, the next cell diagonally, and the list area. The list scrolls by itself, every cell is cut out, and a review screen names them in the order of the list's group.

## License

MIT or Apache-2.0, at your option.
