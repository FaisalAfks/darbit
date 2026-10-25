// Themes: switch, cycle, follow other windows, custom tokens. See docs/tasks/T02-tokens-themes.md.
//
// The choice is kept per computer (localStorage, shared by every darbit window on the same origin) and,
// once the local server is running (T05), saved as the `ui.theme` setting, which it broadcasts to every
// window as `theme.changed`.
import "./tokens/tokens.css";
import "./tokens/themes.css";
import "./tokens/motion.css";
import { register } from "./actions";
import { on, request } from "./api";

export const THEMES = ["glass-dark", "glass-light", "midnight", "high-contrast"] as const;
export type ThemeName = (typeof THEMES)[number];

const SAVED = "darbit.theme";
const changeListeners = new Set<(name: ThemeName) => void>();

function isTheme(name: string | null | undefined): name is ThemeName {
  return THEMES.includes(name as ThemeName);
}

function saved(): ThemeName {
  try {
    const name = localStorage.getItem(SAVED);
    if (isTheme(name)) return name;
  } catch {
    // storage blocked: the default theme
  }
  return THEMES[0];
}

/** The theme on this window now. */
export function currentTheme(): ThemeName {
  const name = document.documentElement.dataset.theme;
  return isTheme(name) ? name : THEMES[0];
}

/** Show a theme in this window: the given one, or the one chosen last time. */
export function applyTheme(name: ThemeName = saved()): void {
  document.documentElement.dataset.theme = name;
  changeListeners.forEach((listener) => listener(name));
}

/** Choose a theme for every window: show it here, remember it, and tell the others. */
export function chooseTheme(name: ThemeName): void {
  applyTheme(name);
  try {
    localStorage.setItem(SAVED, name);
  } catch {
    // storage blocked: this window only
  }
  request("settings.set", { key: "ui.theme", value: name }).catch(() => {
    // no server (a window opened on its own): the other windows follow through storage
  });
}

/** The next theme in the list, for ctrl+alt+t and the theme switch. */
export function cycleTheme(): ThemeName {
  const next = THEMES[(THEMES.indexOf(currentTheme()) + 1) % THEMES.length];
  chooseTheme(next);
  return next;
}

/** Called with the new theme whenever this window's theme changes. Returns a function that stops it. */
export function onThemeChange(listener: (name: ThemeName) => void): () => void {
  changeListeners.add(listener);
  return () => changeListeners.delete(listener);
}

/** Tokens from a custom theme.toml (names without `--`), set on top of its base theme. */
export function loadCustomTheme(tokens: Record<string, string>): void {
  for (const [name, value] of Object.entries(tokens)) {
    document.documentElement.style.setProperty(`--${name}`, value);
  }
}

/** Follow the theme chosen in other windows, and register the theme action. Each app calls this once. */
export function startTheme(): void {
  applyTheme();
  window.addEventListener("storage", (event) => {
    if (event.key === SAVED && isTheme(event.newValue)) applyTheme(event.newValue);
  });
  on("theme.changed", (data: { name: string; tokens?: Record<string, string> }) => {
    if (isTheme(data.name)) applyTheme(data.name);
    if (data.tokens) loadCustomTheme(data.tokens);
  });
  register({ name: "view.theme", label: "Next theme", run: () => cycleTheme() });
}
