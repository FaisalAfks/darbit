# T16 Player and live run panel

**Goal:** play run files from a script or on their own, and watch and edit them live in a panel docked to the side of the screen.

**Depends on:** T03, T14. **Issue:** #40. **Milestone:** v0.4. **Keys:** the `[run_panel]` scope.

## Files

- `packages/darbit/src/darbit/runs/player.py`: `play(path_or_run, panel=False)`; also `d.play`
- `packages/ui/src/apps/runpanel/App.svelte`, `StepRow.svelte`
- `packages/darbit/src/darbit/runs/service.py`: `run.load`, `run.control`, `run.edit`, events `run.at`, `run.paused`

## Steps

1. **Player:** walks checkpoints → goals → steps with darbit's own calls (`press`, `hold`, `click`…). Before each checkpoint, `wait(wait_for, timeout)`; if it doesn't show, the run fails at that checkpoint with a step failure (run report, screenshot) and returns `False`. `turn` uses `drag` with the right button or arrow keys as recorded. Window fractions → real pixels from the window's current place (T22).
2. Every step publishes `run.at {checkpoint, goal, step}`; observers' interrupts (v0.2) stop it like any darbit call.
3. **The panel** (`bar` window, docked right, 300 px, collapses to a 40 px rail): the tree of checkpoints, goals, steps; the current step highlighted and kept in view; a time bar per goal.
4. **Control:** `F5` continue, `Shift+F5` stop, `F10` step, `F9` breakpoint on the selected step (saved as `break: true`), `F2` edit (a wait's seconds, a key), `Insert` add a step after the selected one (a picker of step kinds; "turn" offers a dial). All as buttons too.
5. **Edits live:** an edit to a step that hasn't run yet takes effect in this run; `Ctrl+S` saves the file (T14 `dump`).
6. The panel never takes focus from the game (T06 `bar`), so F-keys only work when the panel is clicked; the global `run.pause` works always.

## Contracts

- `d.play(run: str | Path | Flow, panel: bool = False) -> bool`: a `runs/<name>.py` file, or a loaded flow; the same as calling the `@d.flow` function, with the panel and breakpoints ([T14](T14-run-files.md))

## Done when

The Slime run from T15 plays to the end in game; a breakpoint stops it, a wait changed in the panel is used, and the change is saved.

## Tests

- The player with fake input functions: order of calls, breakpoints, a missing checkpoint fails, an interrupt stops it.
