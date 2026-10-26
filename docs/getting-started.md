# Getting started

## Install

darbit runs on Windows with Python 3.11 or newer.

```bash
pip install "darbit @ git+https://github.com/FaisalAfks/darbit#subdirectory=packages/darbit"
```

In a bot managed with [uv](https://docs.astral.sh/uv/), pin it to a release so the bot only changes when you upgrade on purpose:

```toml
# pyproject.toml
[project]
dependencies = ["darbit"]

[tool.uv.sources]
darbit = { git = "https://github.com/FaisalAfks/darbit", tag = "v0.2.0", subdirectory = "packages/darbit" }
```

## A first script

```python
import darbit as d

d.settings.timeout = 10  # how long clicks wait for their target

if d.click("Gui.Play"):  # waits up to 10 s; False if it never shows
    menu = d.wait("Play.Raid", "Roblox.Disconnected")  # the first of several
    if menu and menu.name == "Play.Raid.png":
        d.press("tab")
```

- `Gui.Play` is a **target**: `images/Gui.Play.png` next to the script, plus an optional `Gui.Play.json` with where to look, how similar it must be, and where to click.
- Not finding something returns `None` or `False`. It never raises.
- `Ctrl+Alt+Q` stops the script at once and lets go of every key.

## Capturing targets

```bash
python -m darbit.capture Gui.Play                # one image: the screen freezes after 3 s, box it, Enter
python -m darbit.capture menus/bag --region      # a region
python -m darbit.capture afk/spot --location     # a point
```

Click a button to box it (click again for the next bigger thing), or drag a box; its edges snap onto borders. See [the capture tool](guides/capture.md).

## The smallest bot

[examples/hello-bot](https://github.com/FaisalAfks/darbit/tree/main/examples/hello-bot) is a whole bot in a few lines: its folder layout, a pinned darbit, a target and a loop that stops cleanly.

## The darbit command

```
darbit new my-bot                                  # a project laid out like examples/hello-bot
darbit install https://github.com/me/my-bot        # cloned at its newest release, with its own environment
darbit run                                         # the project here (or above), with its environment
darbit capture Gui.Play | guide | check | report   # the tools, same options as python -m darbit.<tool>
```

`darbit install` puts bots in `%LOCALAPPDATA%\darbit\bots\<name>` and needs git and [uv](https://docs.astral.sh/uv/). See [bot projects](guides/projects.md) for `darbit.toml`.

## Next

- [Targets and calls](guides/targets-and-calls.md): every call and setting.
- [Observers and saved state](guides/observers-and-state.md): react to events, and remember things between runs.
- [Logs, reports and checking a library](guides/logs-and-reports.md): what happened, and how healthy the pictures are.
