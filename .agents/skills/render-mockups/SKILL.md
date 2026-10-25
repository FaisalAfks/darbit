---
name: render-mockups
description: Render docs/ui/mockups.html to PNG images (every section, theme and state) and check them.
---

# Render the mockups

1. `python scripts/render_mockups.py` (or `--only studio` for some shots). It uses headless Microsoft Edge. Images go to `docs/ui/images/`.
2. Look at every image:
   - nothing is invisible or half-faded;
   - no overlaps;
   - tooltips aren't clipped;
   - phone shots (390 px) don't scroll sideways.
3. Things to know:
   - Headless Edge never renders narrower than 504 px; phone shots render inside a 390 px frame and are cropped.
   - The page's screenshot mode (`?shot=<section>&theme=…&view=…&state=…&paused=1&wizard=<step>`) turns animations off. A new section needs its `id` in a `.sec-head`, plus a line in `SHOTS`.
   - Edge's temporary profiles are deleted after each shot.
4. New rules found while reviewing go into `docs/style/ui/design-system.md`.
