# 0016 Image, region, location; and one look for the Studio

Accepted, 2026-11-02.

## Context

The same three things had several names: the files and code said image, region and location, the Studio said
picture, area and point, and the service sent `point`. A Library tab looked for one name while the service sent
another, so it counted wrong. The Library also guessed a target's kind from which fields its file had.

The Studio's floating pills (Capture's, the recorder's, the run pill) were each drawn on their own, and drifted apart:
different colours, see-through glass over the game, one that hid and one that didn't.

## Decision

- **Names:** image, region, location, everywhere: the Studio's words, the docs, the files, the service and the code.
  (SikuliX's words, and the ones the files already used.)
- **Kinds are written down:** a target's settings file names its `kind`. An image is searched in its region (the
  whole screen without one) and clicked at its location (its centre unless moved). `core.targets.kind_of` works out
  the kind of files from before, and `darbit kinds BOT` writes it in.
- **One look:** the Studio's parts are built from a few shared components on the theme's tokens: `FloatingPill` and
  `PillWindow` for every tool over the game, `Segmented`, `PillButton`, `IconButton`, `Chip`. Over a game they're
  solid, never see-through. A new tool uses them instead of drawing its own. The theme choice stays.

## Consequences

- Old names are still read (`point` as a kind, files without `kind`).
- A tool or page that needs something the shared parts don't have extends them, so every tool gets it.
