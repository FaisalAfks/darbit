# 0018 What belongs in darbit, and what in a bot

Accepted, 2026-11-05.

## Context

darbit grew alongside one bot, and the line between them blurred both ways: settings added for that bot's game
(`front`, made for one rejoin), examples and comments in its names, and parts every bot needs (a loop that retries
after a failure, config loading, waits scaled by lag, daily counters) written inside the bot instead of darbit.

## Decision

- darbit holds what any bot for any game would use unchanged: finding, clicking and typing, windows and apps,
  settings and state, runs, logs and reports, recovery, the service and the Studio.
- A bot holds what only makes sense for its game: its screens, modes, timings, rules and names.
- The test: would a bot for a different game want it as it is? Yes: darbit. No: the bot.
- A darbit feature is general from the start: no setting, default or wording that assumes one game. A bot's need is
  met by a general call the bot uses, never by a setting shaped around it.
- darbit's examples, docs and placeholders use neutral names (`Menu.Start`, "Daily quest"), never a real bot's.

## Consequences

- `front` is gone; a bot brings its window forward itself when it needs to (`d.apps.focus`).
- Generic parts written in a bot move into darbit one at a time, each with its issue, and the bot then uses them.
