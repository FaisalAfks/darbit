# T26 Checks while recording

**Goal:** while recording, pause and add a check at that exact point. An image check takes its picture with the capture tool and saves it into the bot's assets.

**Depends on:** T09, T15. **Milestone:** v0.4. **Decision:** [ADR 0007](../decisions/0007-studio-flows-and-actions.md).

## How it's used

1. Recording a run, press `Ctrl+Alt+P` (or the bar's Pause button). Nothing is recorded while paused.
2. Press **Add check** on the recorder bar. A small menu lists the kinds:

   | Check | What it adds |
   |---|---|
   | Image | wait for it, if seen, if not seen, until gone |
   | Colour at a point | the pixel matches a colour |
   | Region changes | anything in an area changes |
   | Text | later, T24 |

3. **An image check** freezes the screen, and the capture overlay (T09) opens with a suggested name (`<run>.check<n>`). After **Save**, the picture goes to the bot's `assets/images/` and the step is inserted into the flow at the paused moment.
4. **Resume.** The steps recorded next come after the check, or inside it for "if seen" (until the next check or `Ctrl+Alt+M`).

## Files

- `src/darbit/runs/recorder.py`: `Recorder.add_check(kind, target)` inserts the check at the current time
- `ui/src/apps/recorder/App.svelte`: the Add check menu
- `src/darbit/runs/service.py`: `record.check` message

## Done when

A recording with two image checks plays back: each check waits for its picture before the next steps.

## Tests

`Recorder` with fake events and checks gives the expected flow: checks in the right places, steps inside "if seen".
