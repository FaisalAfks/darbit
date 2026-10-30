# Capturing targets

Targets (pictures, regions and points) are taken from a frozen screen in darbit Studio's Capture. darbit Studio is being rebuilt ([rebuild plan](../plan-rebuild.md), milestone 4); until the new one is out, capture with v0.4's Studio from a checkout of the `v0.4.0` tag:

```bash
git clone --branch v0.4.0 https://github.com/FaisalAfks/darbit darbit-0.4
cd darbit-0.4
uv run --all-extras darbit app        # Library › Edit › Capture, Retake, or Start setup for a guide
```

In Capture:

- Click a button to box it; click the same spot again for the next bigger thing, right-click for smaller
- Drag a box, move it, resize it from its handles, scale it with the wheel, nudge it with the arrows
- Shift+drag sets the search region, Ctrl+click sets the click point
- Test finds the boxed picture in its region and marks every match with its score
- Save writes the target's `.png` and `.json` into the bot's images folder

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
