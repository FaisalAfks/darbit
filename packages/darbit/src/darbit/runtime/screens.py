"""The screen map: a game's screens, the pictures that prove each one is showing, and the moves between them.

    game = d.Map()
    game.screen("Lobby", "Lobby.Play")
    game.screen("Bag", "Bag.Title")
    game.move("Lobby", "Bag", "Lobby.Bag")         # click Lobby.Bag
    game.move("Bag", "Lobby", lambda: d.press("esc"))
    game.go("Bag")                                 # from wherever the game is; False if it gets lost

`go` finds the screen showing (one look for every screen's proofs), takes the shortest way, and checks each move
arrived. A move that lands somewhere else is no failure: it looks again and takes the way from there. See the
rebuild plan, section 8.
"""

from collections import deque
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Self

from ..core.targets import Pattern
from ..settings import settings
from . import actions, find
from .log import log, record

Proof = str | Pattern
How = str | Pattern | Callable[[], object]
TRIES = 4  # times go looks again and takes a new way after a move landed somewhere else


@dataclass
class Move:
    """One way from a screen to another: a picture to click, or anything to do."""

    start: str
    end: str
    how: How
    note: str = ""

    def do(self) -> bool:
        if callable(self.how):
            result = self.how()
            return result is not False
        return actions.click(self.how)


@dataclass
class Map:
    """A game's screens and the moves between them."""

    screens: dict[str, list[Proof]] = field(default_factory=dict)
    moves: list[Move] = field(default_factory=list)

    def screen(self, name: str, *proofs: Proof) -> Self:
        """A screen, proved by any of these pictures being on screen."""
        if not proofs:
            raise ValueError(f"{name}: a screen needs a picture that proves it's showing")
        self.screens[name] = list(proofs)
        return self

    def move(self, start: str, end: str, how: How, note: str = "") -> Self:
        """A way from `start` to `end`: click this picture, or call this (a key press, an action)."""
        for name in (start, end):
            if name not in self.screens:
                raise ValueError(f"no screen called {name}: add it with screen() first")
        self.moves.append(Move(start, end, how, note))
        return self

    def where(self, timeout: float = 0) -> str | None:
        """The screen showing now (one look at every screen's proofs, waiting up to `timeout`); None if none is."""
        whats = []
        owners = []
        for name, proofs in self.screens.items():
            for proof in proofs:
                whats.append(proof)
                owners.append(name)
        if not whats:
            return None
        found = find.wait(*whats, timeout=timeout)
        if found is None:
            return None
        for proof, name in zip(whats, owners, strict=True):
            if _name_of(proof) == found.name:
                return name
        return None

    def route(self, start: str, end: str) -> list[Move] | None:
        """The fewest moves from `start` to `end` ([] when already there); None when there's no way."""
        if start == end:
            return []
        came_by: dict[str, Move] = {}
        waiting = deque([start])
        seen = {start}
        while waiting:
            here = waiting.popleft()
            for move in self.moves:
                if move.start != here or move.end in seen:
                    continue
                came_by[move.end] = move
                if move.end == end:
                    return _walk_back(came_by, start, end)
                seen.add(move.end)
                waiting.append(move.end)
        return None

    def go(self, end: str, timeout: float | None = None) -> bool:
        """Get to the screen `end` from wherever the game is. False if it can't tell where it is, has no way, or
        doesn't get there after a few tries."""
        if end not in self.screens:
            raise ValueError(f"no screen called {end}")
        wait = settings.timeout if timeout is None else timeout
        for _ in range(TRIES):
            here = self.where(wait)
            if here is None:
                log(f"go {end}: none of the map's screens is showing")
                record("go", to=end, state="lost")
                return False
            if here == end:
                record("go", to=end, state="there")
                return True
            way = self.route(here, end)
            if way is None:
                log(f"go {end}: no way from {here}")
                record("go", to=end, state="no way", start=here)
                return False
            for move in way:
                log(f"go {end}: {move.start} -> {move.end}")
                if not move.do() or self._arrived(move.end, wait) is False:
                    break  # somewhere else: look again and take the way from there
            else:
                if self._arrived(end, 0):
                    record("go", to=end, state="there")
                    return True
        record("go", to=end, state="lost")
        return False

    def _arrived(self, name: str, timeout: float) -> bool:
        return find.wait(*self.screens[name], timeout=timeout) is not None


def _walk_back(came_by: dict[str, Move], start: str, end: str) -> list[Move]:
    way = []
    here = end
    while here != start:
        move = came_by[here]
        way.append(move)
        here = move.start
    way.reverse()
    return way


def _name_of(proof: Proof) -> str:
    if isinstance(proof, Pattern):
        return proof.image if isinstance(proof.image, str) else str(proof.image)
    return str(proof)


default = Map()  # the bot's map, for d.go


def go(end: str, timeout: float | None = None) -> bool:
    """Get to a screen of the bot's map (`d.screens`) from wherever the game is."""
    return default.go(end, timeout)
