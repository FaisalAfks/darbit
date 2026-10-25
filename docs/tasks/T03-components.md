# T03 Components

**Goal:** the shared building blocks every window is made of, each in one Svelte file, using only tokens.

**Depends on:** T02. **Issue:** #45. **Milestone:** v0.3.

## Files

`packages/ui/src/lib/components/`: `Button`, `IconButton`, `Toolbar`, `Chip`, `Keycap`, `Card`, `Toast`, `TextSlot`, `Readout`, `Magnifier`, `ProgressStrip`, `ScoreBadge`, `ThemeSwitch`, `CommandPalette`, `Field`, `List`, `Tree`. Placeholders exist for the first fourteen; add `Field`, `List`, `Tree`.

Plus `packages/ui/src/apps/hub/Gallery.svelte`: a page in the hub (dev only) that shows every component in every state, used for screenshots in PRs.

## Steps

1. **Button / IconButton** take `action` (a keymap action name, e.g. `"capture.confirm"`). They look up its keys in the keymap store (T04) and show a `Keycap` in their tooltip. Clicking runs the same handler the key does: one `actions.run(name)` registry in `$lib/actions.ts`.
2. **Toolbar**: a pill of IconButtons with group separators, `role="toolbar"`, arrow keys move between buttons. It can sit at the top or bottom and flips when the mouse comes near (prop `avoidMouse`).
3. **TextSlot**: `{slot: "tool" | "bot" | "guide", text, from?, image?}` as in the design system. One line, cut with "…", full text on hover or focus. No HTML from bots: text only.
4. **Readout**: a chip with `x, y · w × h` (or `x, y` for a point). Click turns it into four small number fields; Enter applies, Esc cancels. Emits `change`.
5. **Magnifier**: takes the frozen image (an `ImageBitmap`), the mouse position, a zoom (4–16) and the shapes to draw (boxes, points, snap guides). It draws with `imageSmoothingEnabled = false` on a 168 px canvas and draws the shapes in zoomed coordinates, so a box under the mouse shows inside the magnifier too. Shows the pixel's colour and coordinates under the grid.
6. **ScoreBadge**: a score (0–1) coloured by verdict: ok ≥ 0.9, risky ≥ the target's similarity, else missing. Used by highlight, the guide and the library.
7. **CommandPalette** (`ctrl+k`): fuzzy search over every registered action in the current window and its keys; Enter runs it.
8. **Toast**: one line, slot-coloured, stacks at most three, 3 s, never steals focus.
9. **Gallery** page with every component in every theme.

## Contracts

- `actions.run(name)` and `actions.register(name, handler, {label, when})`: every window registers its actions here; keys, buttons, the palette and right-click menus all go through it.
- Component props as written in each placeholder's header comment.

## Done when

- The Gallery shows every component in all four themes, and keyboard-only use works (Tab, arrows, Enter, Esc).
- No component has a colour, size or duration that isn't a token.

## Tests

- `npm run check`; a lint rule (stylelint `declaration-property-value-disallowed-list`) bans hex colours outside `tokens/`.
