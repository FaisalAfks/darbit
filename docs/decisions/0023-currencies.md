# 0023 Currencies: a gain's source, balances, and gains per run

Accepted, 2026-11-10.

## Context

A bot that earns currencies (gems, gold, tokens) wants to show how much it has now, where its gains came from and
what each run gave (#475). darbit already had `d.record.gain(name, amount, total=, icon=)`: a gain's name is what it
is a gain of, summed per day on Results and in the Overview's gain blocks, and read back for the week from history
(only `gain` events, so a week costs little). Nothing said where a gain came from, and the only balance was a gain's
`total`, known only when the bot gained something.

The design round picked all three of its options: A, a Wallet block (each balance now, and today's change); B, a
Gains by source block (one currency's gains split by source, today and the week); C, each run's gains on Results,
with the day's total per source.

## Decision

- **A gain's currency is its name,** as before: no second field for it.
- **`d.record.gain` takes `source=`,** where the gain came from. Without one, its source is the top-level step it was
  recorded in, else "other". Each gain also records the step path it was recorded in (`step`), so its source and run
  are known from the gain alone: the week of gains by source still reads only `gain` and `balance` events.
- **A balance is its own call, `d.record.balance(name, value, icon=)`,** a `balance` event with the step it was read
  in. It's a reading off the screen (the lobby's currency), not a gain: a gain of 0 with `total=` would count as a
  gain on Results, and `total` keeps meaning the balance after that gain. A `d.show` block would be a value of the
  bot's own, drawn on its own, not a currency darbit knows.
- **The Wallet** shows each currency's last balance (a `balance`, or a gain's `total` if newer), from today or the
  week before, with when and in which step it was read. Today's change is what the currency gained today; a
  currency with no gains today shows the change since its first read today, which can be less than 0.
- **Gains by source** splits a currency's gains by source, today and each day of the week, in one order (most first),
  each source a theme colour in turn. More than six sources keep the five biggest and count the rest as "other". The
  currency is picked in the block and kept in the layout (`sources:<name>`).
- **Each run on Results** is a top-level step that gained something: its time, its name with what the gains said
  (a source other than the run, or the step inside it: "Speed Raid · Sakura") and its gains by currency. Gains outside
  every step make a line of their own. The day ends with each source's runs and gains.
- **Both blocks are off until added** in Customize, or placed with `kind = "wallet"` or `kind = "sources"` in
  overview.toml. darbit's own layout never has them.

## Consequences

- Old bots and old history keep working: a gain without `source` or `step` counts under the step open when it was
  recorded on Results and today's Overview, and as "other" in the week before (whose steps aren't read).
- A gain recorded outside a step, or from another thread (an `@d.block`, an observer), has no step: its source is
  "other" unless it says one. Rewards are best recorded inside the step that earned them.
- A bot that uses `source=` or `d.record.balance` needs a darbit that has them.
