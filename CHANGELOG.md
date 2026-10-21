# Changelog

## Unreleased

- `python -m darbit.tools.check`: every target scored in its region and everywhere else, against the live screen or saved screenshots, with a verdict and a history
- Waiting for several targets takes one screen capture per look, covering all their regions
- `d.State(name)`: saved values, counters, daily and weekly resets, timers; kept in `settings.state`
- Observers: `d.observe(image or condition)` watches in the background; the next darbit call raises `Interrupted` and held keys are let go; `d.no_interrupts()` for quiet blocks

## 0.1.0 - 2026-10-21

First version: what a SikuliX script needs, in Python.

- Targets: images, locations, or both, loaded by name from the image folders, with an optional `.json` for region, similarity and click offset
- Finding and waiting: `exists`, `wait` (one or several targets), `vanish`, `find_all`, `check`; not found is `None` or `False`
- Mouse: `click`, `double_click`, `right_click`, `hover`, `drag`, `scroll`, with a gliding mouse
- Keyboard: `press`, `hold`, `release`, `write`; keys by position, any keyboard language
- Apps: `apps.open`, `apps.close`, `apps.running`, `apps.focus`, `apps.window`
- Settings, stop hotkey (Ctrl+Alt+Q), `sleep`, keeping the PC awake, releasing keys on exit, an optional window that must be in front
- Real screen pixels on scaled displays
- Log file per day and a screenshot when a long wait runs out
- Capture tool: single targets, guided sessions from a list file with a hiding card, one shot per screen, click to box, snapping, live check, undo and cleanup, and harvesting scrolling lists
