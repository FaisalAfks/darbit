# T13 Retire the Tk capture tool

**Goal:** once the web capture tool does everything people use, remove the Tk one and keep the command the same.

**Depends on:** T09, T10, T12. **Milestone:** v0.3.

## Steps

1. Check parity with the owner: click to select, snapping, zoom, sessions through the guide, undo, nudge. (The grid harvest and `--from` were already removed: they weren't used.)
2. `python -m darbit.capture NAME [--location|--region]`, `--guide FILE` and `--list FILE` (read as a guide via `convert_list`) open the web tool. Keep the flags; drop the ones without a use.
3. Delete `capture/overlay.py`, `capture/session.py` and the Tk parts of `capture/common.py`; keep `store.py` (the files and their undo) and `engine/`.
4. Move the tests that still apply to `test_capture_engine.py`; delete the Tk ones.
5. README: the capture section shows the new tool with a screenshot.

## Done when

`import tkinter` appears nowhere in `src/darbit`, and the capture commands in the README work.
