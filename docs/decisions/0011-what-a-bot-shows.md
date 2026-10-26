# 0011 What a bot shows in the Studio

Accepted, 2026-10-26.

## Context

The Studio's mockups showed a running bot's state, progress, modes and history, but nothing said where that comes from. A bot's author needs a short, plain way to show what matters, and a bot with no extra work should still look useful. The live install also runs from a terminal, not only from the Studio, so the Studio must be able to show a bot it didn't start.

## Decision

**The run report is the one source.** Everything the Studio shows about a running bot comes from what darbit already writes to `.darbit/logs/report-<day>.jsonl` (and the log and screenshots next to it). The Studio follows those files; when it started the bot itself, the same events also arrive live through the local server (T05, T20), only faster.

**Most of it needs no new code.** What each part of a bot's life shows, and where it comes from:

| Part | Shown as | Comes from | The author writes |
|---|---|---|---|
| Who it is | name, accent, version, the app it plays | `darbit.toml` `[bot]` | existing |
| Setup | "164 / 165 pictures", what's missing | `guide.toml` and the images folder | existing |
| Settings | a form, grouped | `settings.toml` (T18) | existing plan |
| Now | a breadcrumb: `Speed Raid › Sakura › Fight`, and for how long | nested `d.step(...)` | existing |
| Round | each top-level step: last run, how long, ok or failed | `d.step(...)` in the report | existing |
| Activity | a feed of what happened | `d.record(event, **fields)` | existing |
| Failures | the reason and the screenshot | a step that raised, `d.screenshot(...)` | existing |
| Watching | each observer and whether it fired | `d.observe(...)` | existing |
| Library | every picture's health | `darbit check` | existing |
| History | days, runs, failures | run reports | existing |
| Progress | a ring or bar: "31 of 133 this week" | **`d.progress(label, done, total)`** | new |
| Next up | "Raid at 12:00", "weekly reset Monday 07:00 UTC" | **`d.next(label, at)`** | new |
| Buttons | "Rescan the Speed Raid list" | `@d.action(...)` (T29) | existing plan |

**Two new calls, both written through `d.record`,** so the report stays the one source and the Studio shows the last known value when the bot isn't running:

```python
d.progress("Speed Raid this week", state.sr_done, 133)  # a ring; again with new numbers to update it
d.next("Weekly reset", reset_time)  # a datetime; shown as "in 2 d 4 h"
```

**`[studio]` in `darbit.toml` only picks and orders.** Without it, the Studio shows Now, Round, Activity, Watching, Setup and every progress the bot reports, in that order. With it, the author chooses the tiles and their labels:

```toml
[studio]
summary = "Raids, Speed Raid, challenges and AFK, all day"
tiles = ["now", "progress:Speed Raid this week", "next", "round", "activity", "watching"]
```

No classes, no dashboard framework: a bot is still a script that calls darbit.

## Consequences

- hello-bot gets a useful page for free: Now, Activity, Watching, Setup.
- ad-bot gets its progress ring and next-up tiles by adding two kinds of calls where it already saves `state.json`.
- The Studio never imports or runs a bot's code to show it; it reads files and events. Only `@d.action` buttons (T29) run bot code, in the bot's own process.
- A new task, T30, adds `d.progress`, `d.next`, the `[studio]` table and the defaults; T20 builds the pages on it.
