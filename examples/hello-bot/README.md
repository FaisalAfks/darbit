# hello-bot

The smallest darbit bot, and the layout every bot follows.

```
hello-bot/
  pyproject.toml   darbit pinned to a release
  darbit.toml      its name, version, the darbit it needs, and darbit settings for it
  bot.py           the bot
  images/          its targets (.png + .json), made with the capture tool
  .darbit/         made when it runs: logs, state (not committed)
```

```bash
uv sync                                  # darbit at the pinned release
uv run python -m darbit.capture Hello.Button
uv run python bot.py                     # Ctrl+Alt+Q stops it
```
