# The screen map

A game is a handful of screens with ways between them. Tell darbit what each screen looks like and how to get from one
to another, and the bot asks to *be* somewhere instead of clicking its way there step by step:

```python
import darbit as d

d.screens.screen("Menu", "Menu.Start")  # the Menu is showing when Menu.Start is on screen
d.screens.screen("Bag", "Bag.Title")
d.screens.screen("Shop", "Shop.Title", "Shop.Sale")  # any of these proves it
d.screens.screen("Ad", "Ad.Close")  # a pop-up is a screen too

d.screens.move("Menu", "Bag", "Menu.Bag")  # click Menu.Bag
d.screens.move("Bag", "Menu", "Bag.Back")
d.screens.move("Menu", "Shop", "Menu.Shop")
d.screens.move("Shop", "Menu", lambda: d.press("esc"))  # or anything: keys, an action
d.screens.move("Ad", "Menu", "Ad.Close")

if d.go("Shop"):  # from wherever the game is
    d.click("Shop.Buy")
```

- **`d.go(name)`** looks for every screen's proofs at once to find where the game is, takes the fewest moves, and
  checks each move arrived. A move that lands somewhere else (an ad, a disconnect screen you mapped) isn't a failure:
  it looks again and takes the way from there, a few times. It returns `False` when none of the screens is showing,
  there's no way, or it doesn't get there; it never raises for that. `d.go(name, timeout=5)` waits that long for each
  screen (finding where the game is too) instead of `settings.timeout`.
- **`where()`** says which screen is showing (or `None`), **`route(a, b)`** the moves between two.
- `d.screens` is the bot's map; `d.Map()` makes another.
- Each `go` goes in the run report (`go`: there, lost or no way), so the Overview's activity shows it.
- `d.keep_trying(..., back_to="Menu")` goes back to a screen after a failure and tries again before it
  restarts the game; `back_timeout=` is the `timeout` it gives that `go` ([Trying again](projects.md#trying-again)).

## Testing without the game

`darbit.testing.FakeGame` stands saved screens in for the game: darbit's screen grabs come from the screen showing,
and clicks and key presses move between them. Nothing real is clicked, so a bot's routes are tested in CI:

```python
from darbit.testing import FakeGame


def test_the_shop_is_reached_past_the_ad():
    screens = {"Menu": "tests/screens/menu.png", "Shop": "tests/screens/shop.png", "Ad": "tests/screens/ad.png"}
    with FakeGame(screens, start="Menu") as game:
        game.leads("Menu", "Menu.Shop", "Ad", once=True)  # the first time, an ad pops up
        game.leads("Menu", "Menu.Shop", "Shop")
        game.leads("Ad", "Ad.Close", "Menu")
        assert d.go("Shop") and game.showing == "Shop"
```

The screens darbit Studio saves when you capture (`.darbit/screens`) make good stand-ins. With `window` set, FakeGame
stands in for that window too: looking it up finds a fake one, always in front. Its area is empty, as a minimised
window's, so targets taken in window space stay where they were taken on the saved screens. The desktop is the
screen showing, and the mouse on it starts in its bottom right corner and goes where a click or move puts it
(`game.mouse`, every move in `game.moves`), so `approach` steps back as it would on the PC.

### Real input off

A test that forgets to fake one call still reaches the real PC: a click or key goes to whatever is in front, even a
bot playing live. One line in the bot's `tests/conftest.py` turns real input off for all its tests:

```python
pytest_plugins = ["darbit.testing.no_real_input"]
```

It sets `DARBIT_NO_REAL_INPUT=1` (setting it by hand does the same), for the tests and every process they start.
Then every real input (click, key, mouse move, hold, scroll, drag), app control (`App.open`, `close`, `focus`, and
bringing `window` to the front) and screen grab raises `RealInputOff` naming the call, e.g.
`input.click: real input is off`. Where the cursor is and the desktop's size are a fixed fake: the mouse in the
bottom right corner of a 1920x1080 desktop, so a click with `approach` on is refused as `input.click` too, on any
system. Other calls that only look (which windows are open, `App.running`, the monitors) still work. FakeGame's fakes are used before the switch is checked, so tests on saved screens work as
before. A test that fakes input another way asks for the `real_input` fixture to turn it back on for itself.
