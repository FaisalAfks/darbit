# Targets and calls

What a target is, every call, the settings, and stopping a script.

## Targets

A target is a name like `Gui.Play` or `lobby/play`. It's looked up in the `images` folder next to the script (and the script's own folder): `Gui.Play.png`, plus an optional `Gui.Play.json` with its settings:

```json
{"region": [2133, 404, 428, 1125], "similarity": 0.85, "offset": [0, 12]}
```

- `region`: where to search; without it the whole screen
- `similarity`: lowest score that counts as found, 0 to 1 (default `settings.similarity`)
- `offset`: click point from the image's centre
- `location`: a fixed point, for targets without an image
- `match`: matching options for this target (below)

A target can also be made in code: `d.Target("Bag.Character.png", similarity=0.6)`.

All positions are real screen pixels, also on scaled displays (150% etc.).

### Matching options

By default a picture is found by plain template matching, in full colour, at its own size. Options change that, for one target (`"match"` in its `.json`) or for the whole bot (`[settings.match]` in `darbit.toml`, or `d.settings.match`); a target's own options go on top of the bot's:

```toml
[settings.match]
fast = true
grayscale = true
```

- `grayscale`: match grey pixels; about a third of the work, and colour is ignored
- `fast`: look on smaller copies of the screen and the picture first, then check the best few places at full size
- `colour`: also check the colours, so an icon in other colours isn't taken for this one
- `sizes`: when the picture isn't found at its own size, try other sizes in turn: `true` for 90%, 110%, 80%, 125%, 75% and 133%, or a list like `[0.75, 1.25]`

On the test bench (`bench/README.md`), `fast` and `grayscale` together bring a whole-screen search from about 0.6 s to 15 ms with the same answers. Each option is off until it's asked for, since a game's pictures may behave differently.

`settings.matcher` picks another matcher installed as a plugin (the `darbit.matchers` entry point); the default is `"template"`.

### Other screens and moving windows

The capture tool also saves `scale` (the display scaling) and, with `--window Roblox`, the window's size and corner (`window`, `origin`). Before each search the target is placed on the screen as it is now:

- **Taken in a window** (`window` and `origin` saved) and `settings.window` set (or `[bot] window` in `darbit.toml`): its region, location and click offset follow the window, and the picture is resized by how much wider the window is now
- **Only `scale` saved:** the picture is resized by the change in scaling, and its region grown to fit
- **Nothing changed**, or neither saved: used exactly as it is
- A resized picture that isn't found is tried once at 90–110% of that size; a size that works is kept for the rest of the run
- A window whose shape changed (not just its size) is logged once: such targets may need taking again
- `python -m darbit.tools.check` lists targets taken at another scaling

## Calls

| Call | Does | Returns |
|---|---|---|
| `exists(target, timeout=0, region=None)` | looks for a target, up to `timeout` seconds | `Match` or `None` |
| `find(target, timeout=None, region=None)` | waits for a target, up to `settings.timeout` | `Match` or `None` |
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

`Location(x, y)` is a fixed point. A target can be a name, a `Target`, or a `Pattern`: a name with settings changed in code, on top of its `.json`:

```python
play = d.Pattern("Lobby.Play").similar(0.85).offset(10, 0)  # also .exact(), .within(region), .options(fast=True)
```

### Regions, screens and apps

A `Region(x, y, w, h)` searches and clicks inside itself, the SikuliX way: `exists`, `find`, `wait`, `vanish`, `find_all`, `click`, `double_click`, `right_click`, `hover`, `drag` and `observe` are the calls above with `region=` set to it.

```python
game = d.App("Roblox").window  # a Region, or None if it isn't open
if game.exists(play, timeout=3):
    game.click(play)
d.Region.of(match).grow(40).exists("Close")  # around something found
```

`Screen()` is every monitor together, `Screen(0)` the first. `App(name)` has `window`, `running`, `focus()`, `close()` and `open()`.

Loaded pictures stay in memory; their files are checked at most once a second, so a picture taken again is used from the next search on.

Keys are sent by their position on the keyboard, so games get them and the keyboard language doesn't matter. The mouse glides to each spot, which some games need to register a click.

## Settings

```python
d.settings.timeout = 3  # how long actions wait for a target
d.settings.similarity = 0.7  # default similarity
d.settings.glide = 0.5  # seconds the mouse takes to move
d.settings.scan_rate = 5  # searches per second while waiting
d.settings.window = "Roblox"  # bring this window to the front before any input
d.settings.missing_images = "skip"  # treat a missing image file as never found, instead of an error
d.settings.screenshot_after = 20  # save a screenshot when a wait this long runs out
d.stop_key("ctrl+alt+q")  # the stop hotkey
```

## Stopping

Ctrl+Alt+Q stops a running script: every held key and button is let go and the next darbit call raises `Stopped`, even in the middle of a wait or a sleep. Held keys are also let go when a script ends or crashes. While a script runs, the PC doesn't go to sleep.
