# The screen map

A game is a handful of screens with ways between them. Tell darbit what each screen looks like and how to get from one
to another, and the bot asks to *be* somewhere instead of clicking its way there step by step:

```python
import darbit as d

d.screens.screen("Lobby", "Lobby.Play")  # the Lobby is showing when Lobby.Play is on screen
d.screens.screen("Bag", "Bag.Title")
d.screens.screen("Shop", "Shop.Title", "Shop.Sale")  # any of these proves it
d.screens.screen("Ad", "Ad.Close")  # a pop-up is a screen too

d.screens.move("Lobby", "Bag", "Lobby.Bag")  # click Lobby.Bag
d.screens.move("Bag", "Lobby", "Bag.Back")
d.screens.move("Lobby", "Shop", "Lobby.Shop")
d.screens.move("Shop", "Lobby", lambda: d.press("esc"))  # or anything: keys, an action
d.screens.move("Ad", "Lobby", "Ad.Close")

if d.go("Shop"):  # from wherever the game is
    d.click("Shop.Buy")
```

- **`d.go(name)`** looks for every screen's proofs at once to find where the game is, takes the fewest moves, and
  checks each move arrived. A move that lands somewhere else (an ad, a disconnect screen you mapped) isn't a failure:
  it looks again and takes the way from there, a few times. It returns `False` when none of the screens is showing,
  there's no way, or it doesn't get there; it never raises for that.
- **`where()`** says which screen is showing (or `None`), **`route(a, b)`** the moves between two.
- `d.screens` is the bot's map; `d.Map()` makes another.
- Each `go` goes in the run report (`go`: there, lost or no way), so the Overview's activity shows it.

## Testing without the game

`darbit.testing.FakeGame` stands saved screens in for the game: darbit's screen grabs come from the screen showing,
and clicks and key presses move between them. Nothing real is clicked, so a bot's routes are tested in CI:

```python
from darbit.testing import FakeGame


def test_the_shop_is_reached_past_the_ad():
    screens = {"Lobby": "tests/screens/lobby.png", "Shop": "tests/screens/shop.png", "Ad": "tests/screens/ad.png"}
    with FakeGame(screens, start="Lobby") as game:
        game.leads("Lobby", "Lobby.Shop", "Ad", once=True)  # the first time, an ad pops up
        game.leads("Lobby", "Lobby.Shop", "Shop")
        game.leads("Ad", "Ad.Close", "Lobby")
        assert d.go("Shop") and game.showing == "Shop"
```

The screens darbit Studio saves when you capture (`.darbit/screens`) make good stand-ins.
