# T11 Highlight: what's found, with scores

**Goal:** at any moment, press a key and see on top of the game where each target is found and how well, like SikuliX's `highlight()`, but for many targets at once and with scores. Also callable from a script.

**Depends on:** T03, T06. **Milestone:** v0.3. **Key:** `highlight.toggle` (`ctrl+alt+h`).

## Files

- `packages/darbit/src/darbit/runtime/highlight.py`: `d.highlight(*targets, seconds=3, region=None)` and `scan()`
- `packages/darbit/src/darbit/tools/check.py`: reuse `check_one` for scores (in-region best and best elsewhere)
- `packages/ui/src/apps/highlight/App.svelte`: the click-through overlay
- `packages/darbit/src/darbit/capture/service.py` or `runtime/highlight.py`: server handler `highlight.scan`

## Steps

1. **What's highlighted:** from the hotkey, the targets of the current context: the guide screen being captured (T12), else the project's whole library, else the folder given on the command line. The overlay's small side list switches between them. From a script, the targets passed to `d.highlight`.
2. **Scan fast:** one screen grab; each target is searched only in its region (named or saved); targets without a region are searched at half size first and confirmed at full size near the best spot. Results stream to the overlay as they come (thread pool), so the first boxes show at once. Budget: first box < 100 ms, 150 targets with regions < 1 s. Put numbers in the PR.
3. **Show:** a box per found target in its kind colour with a `ScoreBadge` and its name; risky ones (a high score elsewhere too, as `check` says) get a warning ring; a small corner list counts "not seen: 3" with their names. Boxes appear with a short scale-in and fade after `seconds` (3 by default). The hotkey again, or Esc, hides them.
4. **Click-through by default** (T06 `clickthrough`): the game keeps working underneath. Holding `Ctrl` makes the boxes clickable: a click opens that target in the capture tool to retake it.
5. **From a script:** `d.highlight("Gui.Play", "Gui.Bag")` returns at once and shows for `seconds`; with no server or desktop UI installed it only logs the scores (`highlight Gui.Play 0.97 at 1820,420`). Never raises.
6. **Run report:** each scan records `highlight` events with the scores, so the hub's library shows when a target last scored well.

## Contracts

- `d.highlight(*targets: What, seconds: float = 3, region: Region | None = None) -> list[Match]` (the matches it found, so scripts can use it as a debug `find_all`).
- Message `highlight.scan {targets?, context?} -> stream of highlight.hit {name, box, score, elsewhere, verdict}` then `highlight.done {missing}`.

## Done when

- In game, `ctrl+alt+h` shows every Speed Raid menu target with its score within a second, the game keeps the mouse, and Ctrl+click on one opens it for a retake.
- `d.highlight` works from a bot without the UI extra installed (log only).

## Tests

- `scan()` on saved screens returns the expected boxes and verdicts; timing test marked `slow`.
