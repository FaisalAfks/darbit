# Design system

One look for every surface of darbit Studio: its window and pages, and the tools over the game (Capture, Scout,
the recorder and the run pill). The Studio is Qt (PySide6 and QML): its components are in
`packages/darbit/src/darbit/studio/qml/`, its themes in `packages/darbit/src/darbit/studio/theme.py`. The reference
look is [mockups.html](../../ui/mockups.html), with its tokens in [tokens/](tokens/tokens.css); the Studio's redesign
rounds are in [docs/ui/redesign/](../../ui/redesign/README.md).

## Principles

1. **Small.** A tool covers as little of the screen as it can. The game is the main thing on screen; darbit sits at its edges.
2. **Little to read.** One line of text per thing, short labels, numbers in a monospace font. Longer help lives behind a hover.
3. **Every key is a button, every button has a key.** The command palette names each command's keys. Nothing is keyboard-only.
4. **Light motion.** Only opacity, a short move and scale animate, which the scene graph does without laying anything
   out again. **Smooth effects** off (darbit settings) makes every animation instant, for slower PCs.
5. **Themeable.** Colours come only from the theme. A theme is a set of token values; components never hard-code a colour.

## Themes

| Theme | For |
|---|---|
| `glass-dark` (default) | dark translucent panels, cyan-to-violet accent |
| `glass-light` | the same in light, for bright screens |
| `midnight` | solid near-black panels: the lightest to draw, for slow PCs and OLED |
| `high-contrast` | bright edges, no transparency, bold colours |
| custom | `theme.toml` in darbit's settings folder: `base = "glass-dark"` and any tokens on top (`accent = "#ff7ab6"`) |

darbit settings (or the command palette) picks one, and the Studio keeps it for next time.

## Standards (decision 0012)

- **Sizes follow Fluent 2,** Microsoft's design system for Windows apps: its type ramp
  ([typography](https://fluent2.microsoft.design/typography)) and its spacing, corner, duration and curve tokens
  (`microsoft/fluentui`, `packages/tokens/src/global`). Windows users already know these proportions.
- **Accessibility follows WCAG 2.2 AA:** text 4.5:1 against what it sits on, hint text and indicators 3:1, nothing
  clickable smaller than 24 × 24 px.

## Tokens

The Studio's tokens are colours, from `theme.py`, and every QML file reads them as `studio.colors.<name>`. The names
are the mockups' CSS names in camelCase (`--glass-strong` is `glassStrong`); a custom theme may use either.

| Group | Tokens |
|---|---|
| Surfaces | `bg` (behind everything), `glass` (a card's fill), `solid` (a panel with no see-through), `raised`, `raisedHover`, `line`, `shadow` |
| Text | `text`, `muted`, `faint` |
| Accent | `accent`, `accent2`, `onAccent` (text on the accent) |
| Status | `ok`, `warn`, `danger`, `info`, `onStatus` (text on a status colour) |
| Kinds of target | `kindImage` (the accent), `kindRegion` (`accent2`), `kindLocation` (`ok`) |
| Bot text | `slotBot` (words a bot writes, so it's clear who is talking) |

`solid` and the kinds' colours are made from the others, so a custom theme gets them too. `glassStrong` is only what
`solid` is made from: panels use `solid`.

Sizes, type and motion aren't tokens in QML: the shared components hold them, so a page gets them by using the
component. The mockups' [tokens.css](tokens/tokens.css) lists the Fluent 2 ramps they come from.

## Components

The Studio is built from these. A page or tool uses them rather than drawing its own; one that needs something more
extends them, so everything gets it. `test_the_studio_keeps_one_look` fails on a hand-drawn text field, switch,
dropdown, slider or menu (QML's `TextField`, `Switch`, `ComboBox`, `Slider` or `Popup` outside their component), or on
`glassStrong` where `solid` belongs.

| Component | For |
|---|---|
| `PillButton`, `IconButton` | every button: `kind` primary (the one main action), plain, quiet or danger; a round glyph with a tooltip |
| `Field` | every text field (`round` with an `icon` for search, `quiet` for a name in a heading) |
| `Switcher`, `Stepper`, `ValueSlider`, `Dropdown` | on/off, a number, a number in a range, one of a few |
| `Segmented`, `Toggle`, `Chip` | a choice of a few, a filter that's on or off, a small label |
| `Choice` | a setting that's on or off, with its label and help |
| `Glass` | a card on a page, with an optional small caps title |
| `Ring`, `Bar` | progress: a ring with its number, a thin bar |
| `FloatingPill`, `PillWindow`, `PillBody`, `PillAction`, `PillGuide` | every tool over the game (Capture, the recorder, the run pill, Scout's pill): the pill in its forms (a row, a labelled column, a floating card), its buttons, and the guide shown while it's dragged |
| `ShotTargets` | the targets taken on one shot, as tiles in Capture's pill: a row that scrolls sideways, or two columns that scroll up and down |
| `MenuPanel`, `MenuLine` | a menu that drops down, and its lines |
| `Banner`, `Toast` | a line that needs you; what just happened |
| `PageFrame`, `Backdrop`, `SmoothWheel` | a page in the stack, the background behind every page, the mouse wheel on a list |
| `Setting`, `Block`, `ProblemGroup`, `AssetCard`, `ActionCard`, `StepRow`, `BotRow`, `Avatar` | a page's own rows and cards, built from the above |

## Surfaces and how much screen they take

| Surface | Where | Behaviour |
|---|---|---|
| Studio window | a normal window | the top bar holds the bot menu, the pages (Overview, Library, Results, Settings) and the run control; darbit settings can put the bots in a sidebar, which folds to their squares on a narrow window |
| Sheets | over the Studio | things opened and closed: New bot, Record, the command palette |
| Capture | full screen, over the frozen shot | its pill on an edge (top centre to start); slides out of sight a few seconds after the mouse leaves it |
| Scout | over the screen, click-through | a box and score per match; its pill on an edge, like the run pill |
| Recorder pill | on an edge (top centre to start) | never takes focus from the game |
| Run pill | on an edge while a bot runs | the Studio hides; the pill slides out of sight past its edge a few seconds after the mouse leaves it |

Every pill moves the same way (#384): dragged to any edge it snaps to the edge's centre, its corners or near the
centre on either side, a row on the top and bottom and a labelled column on the sides; dragged past the dashed line
into the middle it floats as a card with more detail and Dock, and never hides. Each keeps its place per pill. An edge
one screen shares with another isn't used: the pill would slide onto the other screen and couldn't come back.
| Ghost cursor | over the game, click-through | a ripple where the bot clicks and the keys it presses, for a moment each |

Everything over a game is `solid`, never see-through. The bot never sees the run pill in its screenshots.

## Motion

| What | How |
|---|---|
| A card appears | opacity and a 14 px rise, eased out, about 300 ms; `delay` staggers a page's cards |
| A page is shown | opacity and an 18 px slide, about 250 ms |
| A menu opens | a 150 ms fade |
| A toast | slides up from the bottom and fades |
| A button is pressed | scales to 96% |
| A pill is grabbed | tilts a little and shakes once, sways with each move, grows to 103%; it takes the shape of the edge it nears; let go, it glides to its place |
| Progress | a ring sweeps and a bar grows to its share; no counting animations |

## Rules

- **No hard-coded colours** in a component: everything is a `studio.colors` token, or a tint of one. Only real colour
  samples (a theme's swatch in darbit settings) use their own.
- **Panels over the game and menus are `solid`.** Cards on a page are `glass`.
- **One line per thing:** long names and paths are cut with "…" (`elide`) instead of widening the window.
- **States:** every list and view has its empty, loading and error states, not only the full one.
- **Names:** Image, Region and Location everywhere; never picture, area or point.
- **The capture overlay:** the shot outside the selection is dimmed, so the inside keeps the game's exact colours; the
  guide, the hint and the pill never overlap.

The mockups are rendered to images with `python scripts/render_mockups.py` (into `docs/ui/images/`); the Studio's own
pages are drawn to PNGs with `darbit.studio.app.shot()`, as the tests do.
