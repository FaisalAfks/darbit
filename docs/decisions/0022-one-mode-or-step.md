# 0022 Running one mode or one step

Accepted, 2026-11-09.

## Context

Testing a fix to one part of a bot meant running its whole round, or editing its code to skip the rest (#318). darbit
already knows a bot's round from what it records: each top-level `d.step` is a row of the Overview's Today's round,
and the steps inside it are its path (decision 0011). It doesn't know them before the bot runs, and the Studio never
runs a bot's code to show something. Nothing told a bot it was started for less than its round.

The design round picked B and C: ▶ on a mode in Today's round, and `Run only <mode>` and `Run step: <mode> · <step>`
in the command palette, with the run pill and the run control saying `only <mode>` while it runs.

## Decision

- **A bot declares its modes and steps in its darbit.toml,** `[modes]`: each mode is the name of a top-level `d.step`,
  with the names of the steps inside it, in order. Declared, not found at run time, so the Studio lists them while
  the bot is stopped, from a file it already reads. A bot without `[modes]` has nothing to run alone.
- **`bot.start` takes `only`,** `{"mode": ...}` or `{"mode": ..., "step": ...}`, checked against `[modes]` before
  anything else (so a wrong one with `replace` stops nothing). `darbit start` has `--only MODE --step STEP`.
- **The bot gets it as `DARBIT_ONLY`,** JSON, in its environment, as it gets `DARBIT_CONTROL`. The service never
  passes on its own: a round has none. An environment variable reaches every way a bot is started (an entry
  function, a module, a script, `uv run`), and a bot run from a terminal can set it too.
- **The bot honours it; darbit doesn't skip anything on its own.** `d.only()` is the `Only(mode, step)` asked for, or
  None for a round; `d.wants(mode, step="")` is whether a mode, or a step of it, runs: always in a round, else only
  the one asked for (a mode with every step of it, or a step with its mode). The bot ends after one pass when
  `d.only()` is set. `d.step` can't skip its own body, and stopping the bot from inside it would skip whatever the
  bot does after the step (saving its state). `d.plan` keeps only the mode asked for.
- **Everything else is a round's:** the one-input-bot rule and its stop-and-start question (decision 0020), Play's
  checks, Stop, the log and the results. The service keeps what a run was started for in `only.json` in its control
  folder, so a service started later still knows; `bots.list` and `bot.status` say it (`only`) and each bot's
  `modes`. A run of one mode or step that fails isn't started again by `[run] restart`: it's a test, not the round.

## Consequences

- A bot that declares `[modes]` needs a darbit that knows it: an older one refuses the darbit.toml's unknown table.
  A bot moves its darbit pin first, then declares its modes and checks `d.wants` where it runs each one.
- A step that needs an earlier one's work (a list open) does that itself, or the bot checks for it: darbit doesn't
  know what a step needs.
- The Studio offers ▶ only on rows of today's round that are declared modes; a mode that hasn't run today is in the
  command palette.
