# Architecture

How darbit's code fits together. The decisions behind it are in [decisions/](../decisions/README.md).

## Layers

```
core       geometry, targets, matching            pure: no screen, no input; easy to test
platform   screen capture, input, windows, DPI,   Windows only; everything that touches the OS
           the stop hotkey
runtime    find, act, wait, observers, state,     what scripts call (darbit/__init__.py re-exports it)
           logs, run report, steps
tools · capture · runs · project                  the tools: library check, report, capture tool,
                                                  run files, bot projects
server     the local server for the UI            only with the `app` extra
desktop    desktop windows (pywebview)            only with the `app` extra
```

A layer only imports from the layers above it in this list. `import darbit` loads `core`, `platform` and `runtime`; the Studio parts load only when used.

## What happens on `d.click("Gui.Play")`

1. **`runtime/actions.py` `click()`** asks `_point()` where to click.
2. **`_point()`** turns the name into a `Target` (`runtime/find.py` `target()` → `core/targets.py` `load()`):
   - finds `Gui.Play.png` in `settings.images`;
   - reads `Gui.Play.json` (region, similarity, click offset);
   - caches the pixels.
3. A target with a picture is **waited for** (`find.wait` → `_search`), up to `settings.timeout`:
   - **`_look()`** grabs one screenshot covering the target's region (`platform/screen.py` `grab()`, with mss, in real pixels);
   - **`core/matching.py` `best()`** scores the picture at every spot (OpenCV `TM_CCOEFF_NORMED` on colour; plain colour difference for single-colour pictures) and keeps the best;
   - a score at or above the similarity is a `Match`. Otherwise the closest is remembered for the log ("closest 0.78 at …"), and the search tries again `settings.scan_rate` times a second.
   - Every wait goes through `platform/safety.py`, so the stop hotkey and observers' interrupts land within a fraction of a second.
4. **The click point** is the match's centre plus the target's offset.
5. **`_front()`** brings `settings.window` to the front, if set.
6. **`platform/input.py` `click()`** glides the mouse there with `SendInput`, in small steps over `settings.glide` seconds (some games ignore a jump), then presses and releases.
7. The click is written to the day's log and to the run report (`runtime/log.py`), and `True` is returned. Not found means `False`, never an exception.

## Where things are kept

| What | Where |
|---|---|
| target images | `images/` next to the script (`settings.images`) |
| logs, screenshots, run reports | `<project>/.darbit/logs/` (`settings.logs`) |
| saved state | `<project>/.darbit/state/` (`settings.state`) |
| user settings, keymap, themes | `%APPDATA%\darbit\` (`paths.config_dir()`) |
| Studio data, installed bots, cache | `%LOCALAPPDATA%\darbit\` (`paths.data_dir()`, `bots_dir()`, `cache_dir()`) |

## Background threads

- **The stop-key watcher** (`platform/safety.py`) starts with the first darbit call that can be stopped. It also keeps the PC awake.
- **Observers** (`runtime/observe.py`) look every half second, with one screenshot shared by all image observers. They never act themselves: they post an interrupt, and the script's next darbit call raises `Interrupted`.
