// Keys from packages/darbit/src/darbit/keymap.toml (GET /keymap), matched in every window. See docs/tasks/T04-keymap.md.
import { run } from "./actions";

export type Keymap = Record<string, Record<string, string>>;

let keymap: Keymap = {};
let scope = "app";

export function setKeymap(keys: Keymap, windowScope: string): void {
  keymap = keys;
  scope = windowScope;
}

/** The keys for an action, for tooltips and keycaps: "ctrl+alt+c".
 *  [global] and [app] use full names ("capture.freeze", "edit.undo"); the other scopes use names inside
 *  the scope, so "capture.confirm" is [capture] "confirm". */
export function keysFor(action: string): string | undefined {
  const dot = action.indexOf(".");
  return keymap.global?.[action] ?? keymap.app?.[action] ?? keymap[action.slice(0, dot)]?.[action.slice(dot + 1)];
}

/** Whether a key event is the given combination, e.g. "ctrl+enter". */
export function matches(event: KeyboardEvent, keys: string): boolean {
  // TODO(T04): modifiers in order ctrl, shift, alt, win; key names as platform/keys.py; "arrows"
  return false;
}

export function listen(): () => void {
  const onKey = (event: KeyboardEvent) => {
    for (const table of [keymap[scope] ?? {}, keymap.app ?? {}]) {
      for (const [action, keys] of Object.entries(table)) {
        if (keys && matches(event, keys) && run(table === keymap.app ? action : `${scope}.${action}`)) {
          event.preventDefault();
          return;
        }
      }
    }
  };
  window.addEventListener("keydown", onKey);
  return () => window.removeEventListener("keydown", onKey);
}
