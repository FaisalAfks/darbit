# Design system

One look for every darbit surface: the hub app, the capture tool, highlight, the recorder bar, the run panel and the VS Code webviews. Everything here lives in `packages/ui/src/lib/tokens/` and `packages/ui/src/lib/components/`. The mockups are in [mockups.html](../../ui/mockups.html).

## Principles

1. **Small.** A tool covers as little of the screen as it can. The game is the main thing on screen; darbit sits at its edges.
2. **Little to read.** One line of text per thing, short labels, numbers in a monospace font. Longer help lives behind F1 or a hover.
3. **Every key is a button, every button has a key.** Hovering a button shows its keycap. Nothing is keyboard-only.
4. **Light motion.** Only `transform` and `opacity` animate, so the GPU does it and nothing is laid out again. Nothing moves for more than 240 ms. `prefers-reduced-motion` turns motion into fades.
5. **Themeable.** Colours come only from tokens. A theme is a set of token values; components never hard-code a colour.

## Themes

| Theme | For |
|---|---|
| `glass-dark` (default) | dark translucent panels with blur, cyan-to-violet accent glow |
| `glass-light` | the same in light, for bright screens |
| `midnight` | solid near-black panels without blur: the lightest to draw, for slow PCs and OLED |
| `high-contrast` | thick borders, no transparency, bold text |
| custom | a `theme.toml` in the user's folder or a bot's project, overriding any tokens (e.g. a bot's own accent) |

`ctrl+alt+t` cycles themes; the hub's Settings picks one. A theme is a `[data-theme="..."]` block of CSS variables in `themes.css`.

## Tokens

| Group | Tokens |
|---|---|
| Surfaces | `--bg` (behind everything), `--glass` (panel fill), `--glass-strong` (popovers), `--raised`, `--raised-hover`, `--line`, `--blur`, `--shadow` |
| Text | `--text`, `--muted`, `--faint` |
| Accent | `--accent`, `--accent-2`, `--glow` (the accent's shadow), `--on-accent` (text on the accent) |
| Status | `--ok`, `--warn`, `--danger`, `--info`, `--on-status` (text on a status colour) |
| Target kinds | `--kind-image`, `--kind-region`, `--kind-point`, `--handle-fill` (resize handles) |
| Capture | `--screen-dim`: the frozen screen outside the selection, 42% brightness, the **same in every theme** (a light theme must not wash the game out) |
| Text slots | `--slot-tool`, `--slot-bot`, `--slot-guide`, `--on-bot` (text on a bot's accent) |
| Type | `--font`, `--font-strong`, `--mono`; sizes `--size-xs` 11, `--size-s` 12, `--size-m` 14, `--size-l` 18, `--size-xl` 24 |
| Space | `--space-1` 4 … `--space-6` 32 |
| Shape | `--radius-s` 6, `--radius-m` 10, `--radius-l` 16, `--radius-pill` |
| Motion | `--fast` 120 ms, `--move` 200 ms, `--spring` (an overshooting curve for things that appear), `--ease` |

## Text slots

Text on any surface comes from one of three sources, and each looks different, so it's always clear who's talking:

| Slot | Who writes it | Looks like | Example |
|---|---|---|---|
| `tool` | darbit itself | muted, small | "click to box · drag to draw" |
| `bot` | a bot, through the API (`d.capture(..., say=...)`, `d.notify`) | a chip with the bot's name and accent | **ad-bot** · Open the bag first |
| `guide` | the person who wrote the setup guide | body text, with an optional example picture | "The whole Bag window, with some room around it." |

The `TextSlot` component takes `{slot, text, from?, image?}`. Text is cut at one line with "…" and opens fully on hover or focus. Bots can't style their text; they only choose words and an accent.

## Surfaces and how much screen they take

| Surface | Where | Size | Behaviour |
|---|---|---|---|
| Capture toolbar | bottom centre of the frozen screen | one pill, ≤ 560 px wide | moves to the top when the mouse goes near it |
| Readout chips | attached to each box or point | one line | `x, y · w × h`; click to type exact numbers |
| Magnifier | next to the mouse | 168 px | follows the mouse; `z` pins it; shows the boxes too |
| Guide card | top centre | ≤ 420 × 120 px | hides into a 6 px progress strip when the mouse is away |
| Highlight | over the screen, click-through | only the boxes | a score badge per match; fades after 3 s unless pinned |
| Recorder bar | top centre | one pill, ≤ 360 px | never takes focus from the game |
| Run panel | docked to a side | 300 px wide | collapses to a 40 px rail; never takes focus |
| Hub | a normal window | 960 × 640, down to 720 × 480 | `ctrl+.` shrinks it to a mini pill with run, pause, stop and status |

## Components

`Button`, `IconButton`, `Toolbar`, `Chip`, `Keycap`, `Card`, `Toast`, `TextSlot`, `Readout`, `Magnifier`, `ProgressStrip`, `ScoreBadge`, `ThemeSwitch`, `CommandPalette`, `Field` (for generated forms), `List`, `Tree`. Each is one `.svelte` file with no outside dependency; Konva is only used inside the capture canvas.

## Motion

| What | How |
|---|---|
| A panel appears | from 8 px away and 96% size to its place, `--spring`, 200 ms |
| A panel hides | opacity and 8 px, 120 ms |
| Focus, current item | the accent glow grows in, 120 ms |
| Progress | the strip's fill slides; no counting animations |
| Highlight | boxes draw in with a short scale from 104%, then sit still |

## Rules from the 2026-10-25 review

Found while reviewing the mockups (and in a second pass by Gemini). Every component follows them.

- **Tooltips** come from one layer at the top of the page (or window), placed with `position: fixed` and kept inside the viewport, flipping below when near the top. No panel's `overflow` can clip them. A tooltip shows the action's name and its keys.
- **Focus** is a 2 px `outline` in `--accent` with 2 px offset, on `:focus-visible` only. Never a glow alone: Windows high-contrast mode removes shadows.
- **Names:** every icon-only button has an `aria-label`; toggles use `aria-pressed`, tabs `aria-selected`, the current section `aria-current`.
- **Colour scheme:** each theme sets `color-scheme` (light or dark), so scrollbars and form controls match. Under `@media (forced-colors: active)` panels get a `CanvasText` border and the selected item a `Highlight` outline; only real colour samples use `forced-color-adjust: none`.
- **No hard-coded colours** outside the token files, including handles, badges and avatars. Tints are mixed with `color-mix(in oklab, …)`.
- **Motion:** at most 200 ms, `transform` and `opacity` only. A keyframe animation always states its end values (`to { … }`), so an element never ends up invisible. Reduced motion turns movement into 80 ms fades.
- **The capture overlay:**
  - the selection dims everything outside it with `box-shadow: 0 0 0 100vmax var(--screen-dim)`, so the inside keeps the game's exact colours;
  - linked regions and labels sit above the dimming;
  - the guide card, the hint, the region label and the toolbar never overlap;
  - the kind switch never wraps;
  - on narrow screens the toolbar scrolls sideways and the hint and magnifier hide.
- **Shrinking:** grid and flex children that hold code, logs or long names get `min-width: 0`, so they scroll or cut with "…" instead of widening the window.
- **Phone width (≤ 760 px):** single columns, the Studio's rail becomes a bottom tab bar, palettes become two columns. Mockup images of phone layouts are rendered at 390 px.
- **States:** every list and view designs its empty, loading and error states, not only the full one (see the Studio's state switch in the mockups).
- **`[hidden]` always hides,** even on elements with their own `display`.

## Room (2026-10-26 round)

Some screens felt cramped and hard to read, so the Studio and the overlays got more room:

- **Studio type:** 15 px body, 28 px view titles, 16–18 px card titles; buttons at least 36 px high.
- **Labelled navigation:** a 224 px sidebar with icons and names, and the running bot's status at its foot. On a phone it becomes a bottom tab bar.
- **The running bot first:** Home opens on a large card with what the bot is doing, its week (a ring) and its controls, then today's timeline, then every installed bot.
- **One action per row** in a flow, 54 px high, with an icon per kind. The chosen step's details open in a panel on the right, instead of editing everything inline.
- **Lists on demand:** the steps you can add open from an **Add step** button, not a column that is always there.
- **Overlays:** the capture toolbar, recorder bar and run panel use 36 px buttons and 14–15 px text; the guide card is up to 390 px wide.

The mockups are rendered to images with `python scripts/render_mockups.py` (into `docs/ui/images/`).

## The Studio shell (2026-10-26)

The Studio uses the same language as the tools, so it feels like one product:

- **Over the bot's own screen:** glass panels float over the bot's last screenshot, blurred and tinted. Midnight and high-contrast use a solid background instead.
- **A pill menu on top,** shaped like the capture toolbar: the bot switcher (which replaces a Bots page), the sections (Overview, Flows, Library, Runs, Settings), the run controls, and two buttons: **‹/›** shows where each tile's data comes from, the gear opens the Studio's own settings.
- **A dock at the bottom** with every tool (Capture, Highlight, Record, Play, Guide, Check), the same pill as the recorder bar.
- **The Overview is a grid of tiles the bot fills** ([decision 0011](../../decisions/0011-what-a-bot-shows.md)): Now (the step breadcrumb and last screenshot), Progress (rings and bars), Today's round, Next up, What happened, Watching. A tile with nothing to show isn't drawn.
- **Sheets, not pages,** for things you open and close: the bot switcher, the Studio settings, Add step.
