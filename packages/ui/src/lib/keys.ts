// How keys are written for people: "ctrl+alt+c" -> ["Ctrl", "Alt", "C"]. Used by Keycap and tooltips.

const NAMES: Record<string, string> = {
  ctrl: "Ctrl",
  alt: "Alt",
  shift: "Shift",
  win: "Win",
  enter: "⏎",
  esc: "Esc",
  tab: "Tab",
  space: "Space",
  arrows: "↑↓←→",
  delete: "Del",
  backspace: "⌫",
  pagedown: "PgDn",
  pageup: "PgUp",
  click: "Click",
  "right-click": "Right-click",
  drag: "Drag",
};

export function keyNames(keys: string): string[] {
  const names: string[] = [];
  for (const part of keys.split("+")) {
    const key = part.trim().toLowerCase();
    names.push(NAMES[key] ?? key.toUpperCase());
  }
  return names;
}
