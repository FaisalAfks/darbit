# The capture tool

Taking target images, regions and points from a frozen screen. The web version is in [tasks T09–T12](../tasks/README.md).

## Capture tool

```
python -m darbit.capture Gui.Play                 # one image: the screen freezes after 3 s, box it, Enter
python -m darbit.capture afk/spot --location      # a point
python -m darbit.capture --list capture.txt       # a session through a list of targets
```

A list file has one target per line, a description after `#`, grouped by the screen they're on:

```
[Lobby]
Gui.Play                 # lobby: the Play button
location: afk/spot       # where to click to stay active
region: menus/bag        # the bag window
```

In a session, a card at the top of the screen shows the next target. Open its screen and press F8: the screen freezes and every target on that screen is taken from the same shot.

- Click a button to box it; click the same spot again for the next bigger thing (up to whole windows), right-click for smaller
- Or drag a box; its edges snap onto borders nearby (hold Alt to stop)
- Shift+drag sets the search region, Ctrl+click sets the click point (R then drag, C then click work too)
- Regions and points show their position and size; the magnifier shows the boxes too
- Arrows move the box by a pixel, Shift+arrows resize it
- Enter saves and goes to the next target; the image is checked on the live screen right away
- Space takes a new shot, Tab skips, Backspace undoes, Esc goes back to the card
- On the card: `+ Add` adds a target to the session and the list; Done (or Ctrl+Alt+Q) keeps or deletes the session's captures

## Setup guides

A bot can ship a `guide.toml`: the screens to open, in order, and what to take on each. A new user follows it to set the bot up.

```
python -m darbit.capture --guide guide.toml       # a session through every target not captured yet
python -m darbit.capture --guide capture.txt      # turn a list file into guide.toml next to it, once
```

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
- Converting a list keeps its `[screens]` and notes; a run of 5 or more images like `SR.Char.*`, whose notes only repeat their names, becomes one `images` item
