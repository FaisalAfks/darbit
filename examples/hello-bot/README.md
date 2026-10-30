# hello-bot

The smallest darbit bot, laid out the way every bot is.

```
hello-bot/
  pyproject.toml     darbit pinned to a release; the bot as a package
  darbit.toml        its name, entry, the darbit it needs, and darbit settings for it
  guide.toml         what to capture, screen by screen
  src/hello_bot/     the bot's code
  assets/images/     its targets (.png + .json), made with the capture tool
  .darbit/           made when it runs: logs, state (not committed)
```

```bash
uv sync                                                # darbit at the pinned release
# take the button's picture in darbit Studio's Capture (docs/guides/capture.md)
uv run darbit run                                      # Ctrl+Alt+Q stops it
```
