"""`d.Region`: a rectangle on the screen that searches and clicks inside itself, the SikuliX way.

    menu = d.Region(442, 277, 1656, 1083)
    if menu.exists("Lobby.Play", timeout=3):
        menu.click("Lobby.Play")

Each method is the module-level call (`d.exists`, `d.click`, ...) with `region=` set to this one.
"""

from dataclasses import dataclass

from ..core import geometry
from ..core.targets import Match
from ..platform import screen
from . import actions, find, observe
from .actions import Spot
from .find import What


@dataclass(frozen=True, eq=False)
class Region(geometry.Region):
    """A rectangle on the screen, in real screen pixels, to search and click inside."""

    @classmethod
    def of(cls, area: geometry.Region | Match) -> "Region":
        """The region of a match, or of any rectangle."""
        if isinstance(area, Match):
            area = area.region
        return cls(area.x, area.y, area.w, area.h)

    def exists(self, what: What, timeout: float = 0) -> Match | None:
        """The target if it's in this region, looking for up to `timeout` seconds (0: one look)."""
        return find.exists(what, timeout, self)

    def find(self, what: What, timeout: float | None = None) -> Match | None:
        """The target once it's in this region, waiting up to `timeout` (default settings.timeout)."""
        return find.find(what, timeout, self)

    def wait(self, *whats: What, timeout: float | None = None) -> Match | None:
        """Wait for a target, or the first of several, in this region."""
        return find.wait(*whats, timeout=timeout, region=self)

    def vanish(self, what: What, timeout: float | None = None) -> bool:
        """True once the target is gone from this region."""
        return find.vanish(what, timeout, self)

    def find_all(self, what: What) -> list[Match]:
        """Every place the target is in this region, best first."""
        return find.find_all(what, self)

    def click(self, what: Spot, timeout: float | None = None) -> bool:
        return actions.click(what, timeout, self)

    def double_click(self, what: Spot, timeout: float | None = None) -> bool:
        return actions.double_click(what, timeout, self)

    def right_click(self, what: Spot, timeout: float | None = None) -> bool:
        return actions.right_click(what, timeout, self)

    def hover(self, what: Spot, timeout: float | None = None) -> bool:
        return actions.hover(what, timeout, self)

    def drag(self, what: Spot, to: Spot, timeout: float | None = None) -> bool:
        """Drag from a spot found in this region to another spot (found anywhere)."""
        return actions.drag(what, to, timeout, self)

    def observe(self, what: What, name: str | None = None) -> observe.Observer:
        """Watch this region for the target, and interrupt the script when it shows up."""
        return observe.observe(what, name, self)


def Screen(number: int | None = None) -> Region:
    """The whole screen as a region (every monitor), or one monitor: `Screen(0)` is the first."""
    if number is None:
        return Region.of(screen.desktop())
    return Region.of(screen.monitors()[number])
