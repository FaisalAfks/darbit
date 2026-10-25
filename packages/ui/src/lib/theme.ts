// Themes: switch, cycle, custom tokens. See docs/tasks/T02-tokens-themes.md.
import "./tokens/tokens.css";
import "./tokens/themes.css";
import "./tokens/motion.css";

export const THEMES = ["glass-dark", "glass-light", "midnight", "high-contrast"] as const;
export type ThemeName = (typeof THEMES)[number];

export function applyTheme(name: ThemeName = "glass-dark"): void {
  document.documentElement.dataset.theme = name;
}

export function cycleTheme(): ThemeName {
  const now = (document.documentElement.dataset.theme ?? THEMES[0]) as ThemeName;
  const next = THEMES[(THEMES.indexOf(now) + 1) % THEMES.length];
  applyTheme(next);
  // TODO(T02): save through settings.set "ui.theme" so every window follows (theme.changed)
  return next;
}

export function loadCustomTheme(tokens: Record<string, string>): void {
  for (const [name, value] of Object.entries(tokens)) {
    document.documentElement.style.setProperty(`--${name}`, value);
  }
}
