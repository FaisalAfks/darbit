# 0017 The Overview is blocks: the bot lays them out, the person arranges them

Accepted, 2026-11-02.

## Context

A bot's Overview was nine fixed tiles; the author could only pick and order them, the person using the bot could
change nothing, and a bot had no way to show a value of its own.

## Decision

- The Overview is blocks in rows of 12. A block has a kind (how it's drawn: now, round, list, number, ring, chart,
  text, screen, button), what it shows (now, round, next, failures, watching, activity, screen, `progress:<label>`,
  `gain:<name>`, `block:<name>`, `action:<name>`) and a width.
- The author's default is `overview.toml`; without one, the older `[studio] tiles` order it.
- A bot shows values of its own with `d.show(name, value, ...)`, or `@d.block(name, every=)` for a function darbit asks
  while the bot runs. They're run-report events, so the last value shows even when the bot isn't running.
- The service serves the catalog (every block the bot can have today), the author's layout and each block's data
  (`bot.overview`). The Studio keeps the person's own layout per bot in its ui settings, with a way back.

## Consequences

- `[studio] tiles` keeps working; `bot.dashboard` stays for other clients.
- New kinds are added in one place on each side (server/overview.py, Block.qml), for every bot at once.
