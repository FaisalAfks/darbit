# T30 What a bot shows in the Studio

**Goal:** a bot's page in the Studio fills itself from what the bot already reports, plus two small calls for progress and what's next.

**Depends on:** T17. **Milestone:** v0.5. **Decision:** [0011](../decisions/0011-what-a-bot-shows.md).

## Files

- `packages/darbit/src/darbit/runtime/show.py`: `progress(label, done, total)`, `next(label, at)`; both call `record("progress", ...)` / `record("next", ...)`
- `packages/darbit/src/darbit/__init__.py`: export them as `d.progress`, `d.next`
- `packages/darbit/src/darbit/project/manifest.py`: read `[studio]` (`summary`, `tiles`)
- `packages/darbit/src/darbit/project/dashboard.py`: from a project and its run reports, the tiles to show and their values (`tiles(project, day) -> list[Tile]`), for the Studio's server (T20)
- `packages/darbit/tests/test_dashboard.py`

## Steps

1. `d.progress` and `d.next`: check the arguments (a label, numbers ≥ 0 with `done ≤ total`; a `datetime`), then record. No other state.
2. `dashboard.tiles`: read the day's report and build, in order: **now** (the open nested steps and since when), **round** (each top-level step's last start, duration and result), **progress** (the last value per label), **next** (the soonest per label, dropping ones in the past), **activity** (the last 50 records that aren't steps, searches or clicks), **failures** (failed steps with their screenshots), **watching** (observers started and fired), **setup** (T12 `progress`).
3. `[studio] tiles` picks and orders them (`"progress:<label>"` picks one progress); unknown names are an error naming them. Without the table, the default order of step 2.
4. ad-bot (its own PR): `d.progress("Speed Raid this week", ...)` where it saves Speed Raid progress, one per daily mode for its attempts, and `d.next(...)` for the weekly reset and the next raid hour.

## Contracts

- Record events `progress {label, done, total}` and `next {label, at}`.
- Tile names: `now`, `round`, `progress`, `next`, `activity`, `failures`, `watching`, `setup`.

## Done when

hello-bot's page shows Now, Activity and Setup with no changes to it; ad-bot's shows its Speed Raid ring, daily attempts and the weekly reset after the ad-bot PR.

## Tests

`tiles` on saved report files: nested steps open and closed, a failed step, progress updated twice, a `next` in the past, `[studio]` order and an unknown tile name.
