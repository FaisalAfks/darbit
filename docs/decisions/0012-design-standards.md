# 0012 The UI follows Fluent 2's scales and WCAG 2.2 AA

Accepted, 2026-10-26.

## Context

The first components used hand-picked sizes: about 30 different pixel values for spacing, corners and heights. Nothing said why a button was 36 px or a tile's corner 20 px, so screens drifted and felt uneven. A contrast check of the four themes found 9 pairs below WCAG in glass-light and midnight.

## Decision

- **Fluent 2's scales** (Microsoft's design system for Windows apps) for type, spacing, corners, control heights, durations and easing curves. darbit is a Windows tool, so its proportions match what Windows users already know. The values come from Fluent's own sources: the [typography page](https://fluent2.microsoft.design/typography) and `microsoft/fluentui` `packages/tokens/src/global`.
- **16 px text for the Studio's content** (Fluent's Subtitle 2), 14 px for controls and the overlays over the game, 12 px for chips, keys and hints.
- **WCAG 2.2 AA** for accessibility: 4.5:1 for text, 3:1 for hint text and indicators, 24 × 24 px smallest targets, a visible focus outline.
- **Checked on every build:** a raw pixel size in a component or a contrast pair below the line fails `npm run check`.
- darbit keeps its own look (glass, accents, the four themes); only the scales and the accessibility rules come from the standards.

## Consequences

- Components use only tokens; a size used by one component alone is a named custom property at the top of its rule (`--track-width: 44px`).
- Some sizes changed slightly: buttons and icon buttons are 32 px (Fluent's medium), corners 4/8/12/16 px, captions 12 px instead of 11.
- glass-light's faint text, green and amber, and midnight's faint text are darker.
- `docs/ui/mockups.html` keeps its own copy of the old values; Storybook is now the reference for how things look (decision 0005).
