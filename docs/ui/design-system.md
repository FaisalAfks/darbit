# Design system

One look for every darbit surface: the hub app, the capture tool, highlight, the recorder bar, the run panel and the VS Code webviews. Everything here lives in `ui/src/lib/tokens/` and `ui/src/lib/components/`. The mockups are in [mockups.html](mockups.html).

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
| Surfaces | `--bg` (behind everything), `--glass` (panel fill), `--glass-strong` (popovers), `--raised`, `--raised-hover`, `--line`, `--blur` |
| Text | `--text`, `--muted`, `--faint` |
| Accent | `--accent`, `--accent-2`, `--glow` (the accent's shadow), `--on-accent` (text on the accent) |
| Status | `--ok`, `--warn`, `--danger`, `--info` |
| Target kinds | `--kind-image`, `--kind-region`, `--kind-point` |
| Text slots | `--slot-tool`, `--slot-bot`, `--slot-guide` |
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
