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
