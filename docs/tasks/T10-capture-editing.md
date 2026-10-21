# T10 Capture editing: add, undo, nudge, retake

**Goal:** the editing tools of the capture overlay as polished, complete versions: a real history, adding and renaming targets in place, precise moves, and comparing a retake with what's saved.

**Depends on:** T09. **Milestone:** v0.3.

## Files

- `ui/src/apps/capture/history.ts`: the undo and redo stack
- `ui/src/apps/capture/NameField.svelte`: inline name field with autocomplete
- `src/darbit/capture/store.py`: extend `undo()` into a history of file changes (already keeps the bytes it replaced)
- `src/darbit/capture/service.py`: `capture.undo`, `capture.redo`, `capture.rename`, `capture.delete`

## Steps

1. **History, two levels:**
   - in the overlay, every change to the draft (draw, move, resize, link, point) is a step; `Ctrl+Z` / `Ctrl+Y` walk it; the toolbar's undo button shows a count;
   - across the session, every save, rename and delete keeps the bytes it replaced (as `Saved.before` does today), so they can be undone from the toolbar or the guide card, newest first, until the session ends.
2. **Nudge and resize:** arrows move 1 px, `Shift` 10 px; `Ctrl`+arrows resize from the bottom-right, `Ctrl+Shift` 10 px. Holding a key repeats smoothly (one step per animation frame after 300 ms). Each burst of the same key is one history step, not fifty.
3. **Add:** the name chip is an editable field. Typing suggests names from the guide (T12), the bot's code (names in `d.*("...")` calls, scanned by the server), and existing files, with their kind and whether they're captured. A new name is checked (letters, digits, `.`, `_`, `-`, `/` for folders) and added to the guide when there is one.
4. **Rename and delete** from the right-click menu or the chip: rename moves the `.png` and `.json` and updates region links that point to it (T09 step 8); delete asks once and is undoable.
5. **Retake compare:** hold `C` to show the saved image over the new box (T09 step 9); the chip shows the score of the new image against the saved one, and a warning if the size changed by more than 10%.
6. **Save and next:** `Ctrl+Enter` saves and moves to the next guide item without leaving the frozen screen when the next item is on the same screen.

## Contracts

- `capture.undo {} -> {undone}`, `capture.redo`, `capture.rename {from, to}`, `capture.delete {name}`.

## Done when

- Ten edits undo and redo exactly; a rename, a save and a delete in a session are undone in reverse order and leave the folder as it was.
- Holding an arrow moves a box smoothly and is one undo step.

## Tests

- `history.ts` with vitest; Python history of saves, renames and deletes in `tmp_path`, checked byte for byte.
