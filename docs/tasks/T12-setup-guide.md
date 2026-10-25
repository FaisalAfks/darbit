# T12 Setup guide and capture from a bot

**Goal:** replace capture lists with a **setup guide**: an ordered walk-through, written by a bot's author, that tells a new user which screen to open and which images, regions and points to take, in order. And let a bot open the capture tool itself with its own text.

**Depends on:** T09. **Milestone:** v0.3.

## Why

Capture lists were a flat list of names. A new user of a bot needs to know where to go in the game, what each thing is, and the order (e.g. Speed Raid characters in the list's own order, so the list is scrolled once, top to bottom, instead of up and down).

## The guide file: `guide.toml` in the bot's project

```toml
title = "ad-bot setup"
say = "Takes about 15 minutes. Start in the lobby."

[[screen]]
name = "Bag, Characters tab"
say = "Open the Bag and go to the Characters tab."
example = "guide/bag.png"                 # optional picture of what the screen looks like

  [[screen.take]]
  region = "Measure.bagMenuRegion"
  say = "The whole Bag window, with some room around it."

  [[screen.take]]
  location = "Measure.bagSliderLocation"
  say = "The list's scrollbar handle, scrolled to the top."

  [[screen.take]]
  image = "Bag.Character"
  in = "Measure.bagMenuRegion"            # linked region (T09 step 8)

[[screen]]
name = "Speed Raid list"
say = "Open Speed Raid and press Start."

  [[screen.take]]
  images = ["SR.Char.Naruto", "SR.Char.Itadori", "SR.Char.Killua"]   # many images of one kind
  in = "Measure.srMenuRegion"
  order = "list"                          # captured in this order, top to bottom of the game's list
  say = "Each character's card, from the top of the list down."
```

- Kinds: `image`, `images`, `region`, `location`. `in` links a region; `point = "center"` or `[dx, dy]` sets a click offset default.
- `python -m darbit.capture --guide capture.txt` converts an old capture list into `guide.toml` once (screens from `[headers]`, descriptions from `#` comments).

## Files

- `packages/darbit/src/darbit/capture/guide.py`: `Guide`, `load()`, `progress()`, `convert_list()`
- `packages/ui/src/apps/capture/GuideCard.svelte`: the card
- `packages/darbit/src/darbit/capture/service.py`: `guide.open`, `guide.progress`
- `packages/darbit/src/darbit/runtime/capture_api.py`: `d.capture()` and `d.guide()`

## Steps

1. **Load and check** `guide.toml`: unknown keys, duplicate names, `in` pointing at something that isn't a region → clear errors with the line.
2. **Progress** from the files: an item is done when its `.png`/`.json` exists (and, with `--verify`, scores ≥ its similarity on the current screen).
3. **The guide card** (top centre, ≤ 420 × 120 px, hides into a 6 px progress strip when the mouse is away):
   - the screen's name and its `say` (guide slot), with the example picture on hover;
   - the current item: kind icon, name, `say`; for `images` lists, `12 / 133 · next: Sakura` and a strip of the last and next thumbnails;
   - buttons: Capture (`ctrl+alt+c`), Skip, Back, Next (`PgUp`/`PgDn`), Highlight this screen (T11), Undo (T10), Done.
4. **Capturing from the card** opens the overlay with the item's name, kind, linked region and default point already set; `Ctrl+Enter` saves and goes to the next item without unfreezing when it's on the same screen. `order = "list"` keeps the order strictly; a later item can't be captured first without Skip.
5. **From a bot:**
   - `d.capture("Gui.Play", kind="image", say="Box the Play button", region=None) -> Target | None`: opens the overlay for one target (bot slot text), blocks until saved or cancelled. For bots that need a picture taken during a run (a new event banner, a reward).
   - `d.guide("guide.toml", say=None, only=None)`: opens the guide card (for first-run setup); returns when the user presses Done. `only` limits it to some screens.
   - Both need the `app` extra; without it they log what's missing and return `None`.
6. A bot's name and accent on its text come from its project manifest (T17), or `d.settings.name` until then.

## Contracts

- The `guide.toml` format above (bots will ship these files: keep it stable; add keys, don't rename).
- `d.capture`, `d.guide` signatures.

## Done when

- ad-bot's `capture.txt` and `measure.txt` convert into one `guide.toml`, and a fresh folder is set up from it by following the card, including the Speed Raid characters in list order without scrolling back up.
- A test bot calls `d.capture("Test.Thing", say="...")` and gets the saved target back.

## Tests

- `guide.load` errors, `progress` against a `tmp_path` folder, `convert_list` on ad-bot's lists (copied into `tests/data`).
