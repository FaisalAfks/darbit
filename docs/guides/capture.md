# The capture tool

Taking target images, regions and points from a frozen screen. The web version and setup guides are in [tasks T09–T12](../tasks/README.md).

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
