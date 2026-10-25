# 0005 One more HTML concept round, then Storybook with the real components

Accepted, 2026-10-25.

## Context

The UI was designed as a standalone HTML page (`docs/ui/mockups.html`), with a second version made separately. HTML mockups are quick for exploring, but they're throwaway: the real app is built again from scratch, and the two drift apart.

The usual way for component-based UIs:
- design tools such as Figma for designers;
- a component workshop such as Storybook for teams that design in code.

## Decision

1. One last HTML concept round sets the end goal for every screen:
   - capture, highlight, guide, recorder, run panel;
   - the Studio home, with bots, an install wizard and a tools launcher;
   - the flow editor and the export view (ADR 0007).

   `scripts/render_mockups.py` saves every section in every theme as PNG images.
2. Then the real Svelte components are built in `packages/ui` and iterated in **Storybook**, every component in every theme, with screenshots. The HTML mockup is retired once Storybook covers it.

## Consequences

- The end result can be seen and shared before any engine work.
- From then on, what gets designed is what ships.
- `npm install` is needed when step 2 starts.
