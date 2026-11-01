# Capturing targets

A target is an **image**, a **region** or a **location**, taken from a frozen screen in darbit Studio's Capture
(the Library's Capture button, or Ctrl+Alt+C with the game in front). An image is searched in its region (the whole
screen without one) and clicked at its location (its centre unless moved), and all three are made together:

- Pick the kind in the pill: **Image**, **Region** or **Location** (1, 2, 3, or Tab). A ✓ marks each one the target has
- Image or Region: click something to box it, click the same spot again for the next bigger thing, right-click for
  smaller, or drag a box. Location: click where to click
- The kind picked is the one you change: drag inside it to move it, drag its handles, nudge it with the arrows (Shift:
  10 px, Ctrl: its size), Delete removes it. Click a readout to type exact numbers. Ctrl+Z and Ctrl+Y undo and redo
- With Region picked, **Saved ▾** lists the bot's regions: pick a region target to share it by name (images searched
  in the same place move together when it's moved), or another image's region to copy it
- **T** tests the image in its region and marks every match with its score
- **Enter** saves the target's `.png` (an image) and `.json` (its kind, region and location) into the bot's images
  folder

The pill slides out of sight a few seconds after the mouse leaves it; the top edge brings it back. More in the
[Studio guide](studio.md).

## Setup guides

A bot can ship a `guide.toml`: the screens to open, in order, and what to take on each. A new user follows it to set the bot up (Start setup in the Studio).

```toml
title = "my-bot setup"
say = "Start in the lobby."

[[screen]]
name = "Bag"
say = "Open the Bag and go to the Characters tab."

  [[screen.take]]
  region = "Measure.bag"
  say = "The whole Bag window."

  [[screen.take]]
  images = ["Char.Naruto", "Char.Itadori", "Char.Killua"]
  in = "Measure.bag"
  order = "list"
  say = "Each character's card, from the top of the list down."
```

- An item takes one of `image`, `images` (several of one kind), `region` or `location`; `say` tells the user what it is
- `in` names the region the target is searched in; `point` is `"center"` or an offset `[dx, dy]`
- `order = "list"` takes the names strictly in order, so a long game list is scrolled once, top to bottom
- Unknown keys, a name used twice, or `in` naming something that isn't a region stop with a message saying where
- A list file converted to a guide (`capture.guide.convert_list`) keeps its `[screens]` and notes; a run of 5 or more images like `SR.Char.*`, whose notes only repeat their names, becomes one `images` item
