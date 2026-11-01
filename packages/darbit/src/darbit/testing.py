"""Testing a bot without its game: saved screens stand in for the game, and clicks and keys move between them.

    with FakeGame({"Lobby": "screens/lobby.png", "Bag": "screens/bag.png"}, start="Lobby") as game:
        game.leads("Lobby", "Lobby.Bag", "Bag")         # clicking Lobby.Bag on the lobby shows the bag
        game.leads("Bag", "esc", "Lobby", key=True)     # pressing Esc in the bag goes back
        assert my_map.go("Bag") and game.showing == "Bag"

darbit's screen grabs come from the screen showing, and its clicks and key presses go to the fake game instead of
the PC: nothing real is touched. Bots' saved screens (.darbit/screens) make good stand-ins. See the rebuild plan,
section 8 (offline tests).
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Self

import cv2
import numpy as np

from .core import matching
from .core.geometry import Region
from .core.targets import load
from .platform import input as device
from .platform import screen
from .settings import settings


@dataclass
class _Lead:
    picture: str  # a picture to click, or a key to press (`key`)
    to: str
    key: bool = False
    once: bool = False  # a pop-up that shows only the first time


@dataclass
class FakeGame:
    """Saved screens of a game, one showing at a time; clicks and keys lead from one to another."""

    screens: dict[str, str | Path | np.ndarray]
    start: str
    showing: str = ""
    clicks: list[tuple[int, int]] = field(default_factory=list)  # every click, where it landed
    keys: list[str] = field(default_factory=list)  # every key pressed
    _pixels: dict[str, np.ndarray] = field(default_factory=dict)
    _leads: dict[str, list[_Lead]] = field(default_factory=dict)
    _real: dict[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for name, source in self.screens.items():
            pixels = source if isinstance(source, np.ndarray) else cv2.imread(str(source), cv2.IMREAD_COLOR)
            if pixels is None:
                raise ValueError(f"{name}: can't read its screen {source}")
            self._pixels[name] = pixels
        if self.start not in self._pixels:
            raise ValueError(f"no screen called {self.start}")
        self.showing = self.start

    def leads(self, screen_name: str, picture: str, to: str, key: bool = False, once: bool = False) -> Self:
        """On `screen_name`, clicking `picture` (or pressing the key `picture`, with `key`) shows `to`. A lead
        added earlier wins; with `once`, it leads there only the first time (an ad that pops up once)."""
        for name in (screen_name, to):
            if name not in self._pixels:
                raise ValueError(f"no screen called {name}")
        self._leads.setdefault(screen_name, []).append(_Lead(picture, to, key, once))
        return self

    def __enter__(self) -> Self:
        self._real = {"grab": screen.grab, "click": device.click, "tap": device.tap, "move": device.move}
        screen.grab = self._grab
        device.click = self._click
        device.tap = self._tap
        device.move = self._move
        return self

    def __exit__(self, *args: object) -> None:
        screen.grab = self._real["grab"]
        device.click = self._real["click"]
        device.tap = self._real["tap"]
        device.move = self._real["move"]

    def _grab(self, region: Region | None = None) -> tuple[np.ndarray, Region]:
        pixels = self._pixels[self.showing]
        whole = Region(0, 0, pixels.shape[1], pixels.shape[0])
        area = whole if region is None else (region.intersect(whole) or Region(0, 0, 0, 0))
        part = pixels[area.y : area.y + area.h, area.x : area.x + area.w]
        return np.ascontiguousarray(part), area

    def _click(self, x: int, y: int, glide: float = 0, button: str = "left", times: int = 1) -> None:
        self.clicks.append((x, y))
        for lead in self._leads.get(self.showing, []):
            if not lead.key and self._inside(lead.picture, x, y):
                self._follow(lead)
                return

    def _tap(self, what: object) -> None:
        name = str(getattr(what, "name", what)).lower()
        self.keys.append(name)
        for lead in self._leads.get(self.showing, []):
            if lead.key and lead.picture.lower() == name:
                self._follow(lead)
                return

    def _follow(self, lead: _Lead) -> None:
        if lead.once:
            self._leads[self.showing].remove(lead)
        self.showing = lead.to

    def _move(self, x: int, y: int, glide: float = 0) -> None:
        return None

    def _inside(self, picture: str, x: int, y: int) -> bool:
        """Whether (x, y) is on `picture` where it is on the screen showing."""
        target = load(picture, settings.images)
        pixels = self._pixels[self.showing]
        need = target.similarity if target.similarity is not None else settings.similarity
        found = matching.best(target, pixels, Region(0, 0, pixels.shape[1], pixels.shape[0]), need)
        if found is None:
            return False
        return found.x <= x < found.x + found.w and found.y <= y < found.y + found.h
