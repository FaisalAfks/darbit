# darbit

Simple GUI automation for Windows, in Python. Find images on the screen, click, type and wait, the way SikuliX does it, with input that games like Roblox accept.

```python
import darbit as d

d.settings.timeout = 10

if d.click("Gui.Play"):  # waits up to 10 s, False if it never shows
    d.wait("Play.Raid", "Roblox.Disconnected")  # the first of several
    d.press("tab")
    d.press(*"54132")  # game keys, one after another

left = d.exists("Dim.Game.Left", 90)  # a Match, or None
if left:
    d.hold("w")
    d.sleep(2)
    d.release()
```

Not finding something is a normal result: `None` or `False`, never an error.

## Install

```
pip install "darbit @ git+https://github.com/FaisalAfks/darbit#subdirectory=packages/darbit"
```

or, in a project managed with [uv](https://docs.astral.sh/uv/), pinned to a release:

```toml
[tool.uv.sources]
darbit = { git = "https://github.com/FaisalAfks/darbit", tag = "v0.2.0", subdirectory = "packages/darbit" }
```

Python 3.11 or newer, Windows. The repo is a monorepo: the Python package is in `packages/darbit`, the web UI in `packages/ui`.

## Docs

| | |
|---|---|
| [Getting started](docs/getting-started.md) | install, a first script, capturing targets |
| [Targets and calls](docs/guides/targets-and-calls.md) | targets, every call, settings, stopping |
| [Observers and saved state](docs/guides/observers-and-state.md) | interrupting on events, values that survive restarts |
| [Logs, reports, library check](docs/guides/logs-and-reports.md) | what a run leaves behind, and picture health |
| [The capture tool](docs/guides/capture.md) | taking images, regions and points |
| [Architecture](docs/architecture/index.md) | how the code fits together |
| [Decisions](docs/decisions/README.md), [roadmap](docs/roadmap.md), [tasks](docs/tasks/README.md) | why, what's next, and how to build it |

The docs site: <https://faisalafks.github.io/darbit/> (or locally: `uv run --group docs mkdocs serve`).

## License

MIT or Apache-2.0, at your option.
