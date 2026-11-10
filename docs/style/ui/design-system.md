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
4. **Lively, light motion.** Only opacity, a short move and scale animate, which the scene graph does without laying
   anything out again. Motion never changes how anything looks at rest, nothing moves while the window is hidden or
   minimized, and only the live dot moves on its own. **Smooth effects** off (darbit settings) makes every animation
   instant, for slower PCs.
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

Motion is tokens too, the same in every theme: `studio.motion.<name>` is a duration in milliseconds (`pageFade`, `rise`,
`stagger`, `hover`, `glide`, `count`, `sweep`, `grow`, `toast`, `pulse`...) or a curve for `easing.bezierCurve`
(`ease`, `spring`, `decelerate`...), from `DURATIONS` and `CURVES` in `theme.py`. Every duration is 0 while smooth
effects are off or the Studio's window is out of sight, so nothing in it animates then; the pills over the game use
`studio.pillMotion`, which only effects turn off.

Sizes and type aren't tokens in QML: the shared components hold them, so a page gets them by using the component. The
mockups' [tokens.css](tokens/tokens.css) lists the Fluent 2 ramps they come from.

## Components

The Studio is built from these. A page or tool uses them rather than drawing its own; one that needs something more
extends them, so everything gets it. `test_the_studio_keeps_one_look` fails on a hand-drawn text field, switch,
dropdown, slider, menu or sheet (QML's `TextField`, `Switch`, `ComboBox`, `Slider` or `Popup` outside their component), or on
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
| `MenuPanel`, `MenuLine` | a menu that drops down (and the tray panel), and its lines, with their keys on the right |
| `Sheet` | every sheet over the Studio (New bot, Record, Play's checks, Stop and start): one solid frame over the dimmed window |
| `Banner`, `Toast` | a line that needs you; what just happened |
| `EmptyState` | what a page or list shows with nothing in it: a soft glyph in a glass circle, a title, one line of why, and the main action (a button, or a link such as "See yesterday →") with its key from `keymap.toml` under it. It rises in with the cards (`CardMotion`); `compact` is its size in a pill |
| `PageFrame`, `Backdrop`, `SmoothWheel` | a page in the stack, the background behind every page, the mouse wheel on a list |
| `CardMotion`, `MouseLight`, `CountUp`, `LiveDot` | how cards move (the rise, the lift and its shadow), the light following the mouse over a card, a number counting up, a state's dot that pulses while a bot runs |
| `Setting`, `Block`, `ProblemGroup`, `AssetCard`, `ActionCard`, `StepRow`, `BotRow`, `Avatar`, `ScoutTile`, `ScoutLine`, `ScoutDetail` | a page's own rows and cards, built from the above |

## Surfaces and how much screen they take

| Surface | Where | Behaviour |
|---|---|---|
| Studio window | a normal window | the top bar holds the bot menu, the pages (Overview, Library, Results, Settings) and the run control; darbit settings can put the bots in a sidebar, which folds to their squares on a narrow window |
| Sheets | over the Studio | things opened and closed: New bot, Record, Play's checks, Stop and start, the command palette |
| Capture | full screen, over the frozen shot | its pill on an edge (top centre to start); slides out of sight a few seconds after the mouse leaves it |
| Scout | over the screen, click-through, its pill in three forms (a row with a strip of images, a column of groups, a card with a grid) | a box and score per match; its pill on an edge, like the run pill |
| Recorder pill | on an edge (top centre to start) | never takes focus from the game |
| Run pill | on an edge while a bot runs | the Studio hides; a line for each other bot running, with its own controls; the pill slides out of sight past its edge a few seconds after the mouse leaves it |
| Tray panel | by the tray icon, above the taskbar in the work area the pills use, outside the hidden-icons flyout | darbit's menu (`MenuPanel`, `MenuLine`) in its own window; a click outside or Esc closes it |

Every pill moves the same way (#384, #449): dragged to any edge it stays where it's let go along it (pulled onto the
edge's centre or a corner only within 24 points of one), a row on the top and bottom and a labelled column on the
sides, always inside the screen's work area (never under the taskbar); dragged past the dashed line into the middle it
floats as a card with more detail and Dock where it's let go, and never hides. It lands with the pill motion tokens'
spring and eases into a new form while dragged. While it's dragged toward an edge (#467), a dashed ghost of the
pill shows where it lands, in its size and the form it takes there, and only the part of the edge by the mouse glows,
following it. Each keeps its place per pill. An edge
one screen shares with another isn't used: the pill would slide onto the other screen and couldn't come back.
| Ghost cursor | over the game, click-through | a ripple where the bot clicks and the keys it presses, for a moment each |

Everything over a game is `solid`, never see-through. The bot never sees the run pill in its screenshots.

## Motion

The Studio's motion is style B "Lively" of design round 2026-11-09, with C's mouse light and glowing edges (#441).

| What | How |
|---|---|
| A page is shown | fades in (220 ms) and slides up 10 px (320 ms), eased out; the page left fades out and down under it. The page the Studio opens on shows at once: frames drawn at the start stay in its memory for a while |
| A page's cards | fade in and rise 14 px, one after another 45 ms apart, with a little spring (500 ms); again each time the page shows. No scale or turn: Qt draws text a little differently after it has been scaled |
| The selection light | the page light and the sidebar's chosen bot spring to the new choice (380 ms), glowing while they move |
| A card under the mouse | lifts 3 px with a soft shadow, an accent glow and edge (spring, 250 ms); a soft accent light follows the mouse over it |
| A number | counts up from 0 when its page shows, and from the old value to a new one (800 ms, eased out) |
| Progress | a ring sweeps from empty (900 ms); a chart's bars grow from the bottom one after another; a bar grows to its share |
| The live dot | pulses while a bot runs and its window is in sight (1.8 s), stepped 30 times a second |
| A toast | springs up from the bottom and fades where it is when it goes |
| A menu opens | a 150 ms fade |
| A button is pressed | scales to 96% |
| A pill is grabbed | tilts a little and shakes once, sways with each move, grows to 103%; it takes the shape of the edge it nears; let go, it glides to its place |
| Blur-through pages (a setting, off at first) | pages blur out and in from 96%, cards tilt in 70 ms apart; the scale and turn leave text drawn a little differently |
| Aurora (a setting, off at first) | the glass themes' background light drifts slowly back and forth (18 s each way, stepped 10 times a second); never on battery |

## Rules

- **No hard-coded colours** in a component: everything is a `studio.colors` token, or a tint of one. Only real colour
  samples (a theme's swatch in darbit settings) use their own.
- **Panels over the game and menus are `solid`.** Cards on a page are `glass`.
- **One line per thing:** long names and paths are cut with "…" (`elide`) instead of widening the window.
- **States:** every list and view has its empty, loading and error states, not only the full one. Empty is an
  `EmptyState` (#319): the Library and each of its tabs, its Screen view, Results (no runs yet, or none today with
  the way to the last day that has some), the Overview before a bot's first run, an action with no steps, a bot with
  nothing to set, and Scout's pill with nothing in its list.
- **Names:** Image, Region and Location everywhere; never picture, area or point.
- **The capture overlay:** the shot outside the selection is dimmed, so the inside keeps the game's exact colours; the
  guide, the hint and the pill never overlap.

The mockups are rendered to images with `python scripts/render_mockups.py` (into `docs/ui/images/`); the Studio's own
pages are drawn to PNGs with `darbit.studio.app.shot()`, as the tests do.
