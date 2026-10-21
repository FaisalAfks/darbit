# T04 Keymap: every shortcut in one file

**Goal:** one remappable table of every shortcut, used by the Python side (global hotkeys) and every window, with conflicts caught before they happen.

**Depends on:** T01. **Milestone:** v0.3. **Spec:** [docs/ui/keymap.md](../ui/keymap.md).

## Files

- `src/darbit/keymap.toml`: the defaults (written)
- `src/darbit/keymap.py`: `load()` (written), `normalise()`, `conflicts()` (to do)
- `src/darbit/platform/hotkeys.py`: global hotkeys from the `[global]` scope
- `ui/src/lib/keymap.ts`: the keymap store and key matching in windows
- the hub's Settings → Keys page (T20 builds the page; this task builds the editor component `ui/src/lib/components/KeyEditor.svelte`)

## Steps

1. `normalise("Alt+Ctrl+C") == "ctrl+alt+c"`; modifiers in the order ctrl, shift, alt, win; key names as in `platform/keys.py`. Special names: `arrows` (the four arrows), `wheel`, `click`, `drag`, `right-click`.
2. `conflicts(keys)`: the same normalised keys on two actions of the same scope, or a `[global]` key used anywhere else. `load()` logs each conflict and the later layer wins.
3. `platform/hotkeys.py`: `register(keymap["global"], handlers)` with `RegisterHotKey` on one thread with its own message loop (the stop hotkey's watcher already polls; move it onto this). `run.stop` keeps working even if the file is broken: it falls back to `ctrl+alt+q`.
4. The server sends the merged keymap at `GET /keymap` and broadcasts `keymap.changed` after the editor saves.
5. `keymap.ts`: `matches(event, keys)`, `keysFor(action)`, and one `keydown` listener per window that looks up the window's scope plus `app`, then calls `actions.run`.
6. `KeyEditor`: a list of actions by scope with their keys as Keycaps; click one, press the new keys, see a conflict warning before saving. Saving writes the user's `keymap.toml` (only the changed keys).
7. Every placeholder Button already names an action; check none is missing from `keymap.toml` (step in Tests).

## Contracts

- Action names `scope.action` as in `keymap.toml`. Renaming one is a breaking change for users' files: add the new name and keep reading the old one for a version.
- Messages `keymap.changed {keys}`.

## Done when

- Changing `capture.freeze` in the user's file changes the global hotkey and the hint on the capture button, without a restart of the hub.
- A conflicting key is shown in the editor and in the log.

## Tests

- `normalise` and `conflicts` cases; `load()` layering with temp files (`APPDATA` pointed at `tmp_path`).
- A test that every `action="..."` in `ui/src` exists in `keymap.toml` (a regex over the `.svelte` files).
