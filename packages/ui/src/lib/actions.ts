// Every action in a window, in one registry: keys, buttons, the command palette and right-click menus
// all run actions by name, so they always do the same thing. Names match packages/darbit/src/darbit/keymap.toml.

export interface Action {
  name: string; // "capture.confirm"
  label: string; // "Save"
  run: () => void;
  when?: () => boolean; // shown and enabled only when this is true
}

const registry = new Map<string, Action>();

export function register(action: Action): () => void {
  registry.set(action.name, action);
  return () => registry.delete(action.name);
}

export function run(name: string): boolean {
  const action = registry.get(name);
  if (!action || (action.when && !action.when())) return false;
  action.run();
  return true;
}

export function available(): Action[] {
  return [...registry.values()].filter((action) => !action.when || action.when());
}
