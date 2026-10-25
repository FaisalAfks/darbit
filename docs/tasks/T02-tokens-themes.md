# T02 Design tokens, themes and motion

**Goal:** every colour, size and motion value as CSS variables in one place, with four themes and custom themes from a file.

**Depends on:** T01. **Issue:** #45. **Milestone:** v0.3. **Spec:** [docs/style/ui/design-system.md](../style/ui/design-system.md).

## Files

- `packages/ui/src/lib/tokens/tokens.css`: sizes, spacing, radius, motion, fonts (theme-independent)
- `packages/ui/src/lib/tokens/themes.css`: one `[data-theme="..."]` block per theme with every colour token
- `packages/ui/src/lib/tokens/motion.css`: the shared keyframes (`appear`, `hide`, `glow-in`) and the reduced-motion rule
- `packages/ui/src/lib/theme.ts`: `applyTheme(name)`, `cycleTheme()`, `loadCustomTheme(tokens)`
- `packages/darbit/src/darbit/server/app.py`: `GET /theme` returns the custom theme's tokens (T05)

## Steps

1. Fill `themes.css` for `glass-dark`, `glass-light`, `midnight`, `high-contrast`. Every theme defines every colour token in the table in the design system. A test (step 5) fails when one is missing.
2. Glass: `--glass` is a translucent fill used with `backdrop-filter: blur(var(--blur))`. `midnight` and `high-contrast` set `--blur: 0px` and a solid fill, so they cost nothing to draw.
3. `applyTheme` sets `document.documentElement.dataset.theme` and saves the choice through the server (`settings.set` message, key `ui.theme`), so every window and the hub switch together: the server broadcasts `theme.changed` and each app calls `applyTheme`.
4. Custom themes: `%APPDATA%\darbit\theme.toml` or a project's `theme.toml`, a flat table of token names without `--` (`accent = "#ff7ab6"`). The server sends them; `loadCustomTheme` sets them as inline variables on `:root` on top of the base theme named by `base = "glass-dark"`.
5. A small script `ui/scripts/check-tokens.ts` (run in `npm run check`) lists the tokens each theme defines and fails if any theme misses one.
6. Motion: only `transform` and `opacity` in keyframes. `@media (prefers-reduced-motion: reduce)` turns `appear` and `hide` into 80 ms fades.

## Contracts

- Token names as in the design system's table. Components (T03) use only these.
- Message `theme.changed {name, tokens?}`.

## Done when

- The placeholder apps switch between all four themes with `ctrl+alt+t` and the ThemeSwitch, and every open window follows.
- A custom `theme.toml` changes the accent everywhere.

## Tests

- `check-tokens` passes; deleting one token from a theme makes it fail.

## Not in this task

Components beyond the ThemeSwitch.
