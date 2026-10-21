# T15 Recorder

**Goal:** record a run in the game (keys, clicks, camera turns and their timing) into a run file, with checkpoints marked as you go, from a small bar that never takes focus from the game.

**Depends on:** T04, T06, T14. **Issue:** #39. **Milestone:** v0.4. **Keys:** `record.toggle` (`ctrl+alt+r`), `record.mark` (`ctrl+alt+m`), `run.pause` (`ctrl+alt+p`).

## How it's used

1. `darbit record slime` (or the hub's Record button, or `ctrl+alt+r`) shows the recorder bar at the top centre: `● 00:00 · Slime`.
2. Play. Every key, click and camera turn is recorded with its timing.
3. At a point the bot must be sure of (a wave starts), press `ctrl+alt+m`: the screen freezes, click the thing that proves it (click to select, T08), Enter. That's a checkpoint with `wait_for`. The bar shows `· checkpoint 2`.
4. `ctrl+alt+p` pauses (nothing is recorded; the bar shows it); again to go on.
5. `ctrl+alt+r` stops. The run opens in the run panel (T16) for a check, and is saved to `runs/slime.yaml`.

## Files

- `src/darbit/platform/hooks.py`: low-level keyboard and mouse hooks
- `src/darbit/runs/recorder.py`: `Recorder` (events → steps)
- `ui/src/apps/recorder/App.svelte`: the bar
- `src/darbit/runs/service.py`: `record.start`, `record.mark`, `record.pause`, `record.stop`, events `record.tick`

## Steps

1. **Hooks** (`hooks.py`): `SetWindowsHookExW(WH_KEYBOARD_LL)` and `WH_MOUSE_LL` on their own thread with a message loop. Each event: kind, key or button, position in real pixels, `time.perf_counter_ns()`. Hooks must return within a few ms, so they only append to a queue. Skip injected events (`LLKHF_INJECTED`, `LLMHF_INJECTED`) so darbit's own input isn't recorded.
2. **Filter:** drop the recorder's own hotkeys, events over darbit windows, and events when the target window (`window:` in the run, picked when recording starts) isn't in front.
3. **Events → steps** (`recorder.py`), on stop:
   - key down + up within 150 ms → `press`; longer → `hold` … `release`;
   - consecutive presses of letters → `write` when they make a word (optional, off by default for games);
   - gaps → `wait` rounded to 0.05 s; gaps under 30 ms merged;
   - right-button drags → `turn` in degrees (pixels × a per-game factor set in the run, default from a calibration: turn 360° once at the start when asked);
   - arrow keys held for camera → `turn` too when the run says arrows turn the camera;
   - clicks → `click` at window fractions; drags → `drag`.
4. **Checkpoints:** `record.mark` pauses recording, opens the capture overlay with a name `<run>.cp<n>` and kind image, and on save adds a checkpoint with `wait_for` that name. Steps after it go into a new goal under the new checkpoint.
5. **The bar** (`bar` window, T06): red dot pulsing slowly while recording, time, run name, checkpoint count, buttons Mark, Pause, Stop (with their keys on hover). 360 px at most; drag it elsewhere; remembers its place.
6. **Safety:** `run.stop` (`ctrl+alt+q`) stops the recorder too and saves what was recorded as `slime.partial.yaml`.

## Contracts

- Messages above; `Recorder.steps()` returns `list[Step]` from T14's model.

## Done when

A short Slime run is recorded with two checkpoints, saved, and opens in the run panel with sensible steps (presses, holds, waits, turns).

## Tests

- `recorder.py` turns fake event lists into the expected steps (no hooks needed): presses vs holds, merged waits, turns, filtered hotkeys.
- `hooks.py` is tested by hand; describe it in the PR.
