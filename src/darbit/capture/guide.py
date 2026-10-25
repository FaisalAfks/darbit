"""Setup guides: an ordered walk-through of what to capture for a bot. See docs/tasks/T12-setup-guide.md.

    guide = load(Path("guide.toml"))
    progress(guide, Path("images"))      # what's done, what's next
    steps(guide)                         # every target in order, with its screen and text

A guide.toml:

    title = "ad-bot setup"
    say = "Start in the lobby."

    [[screen]]
    name = "Bag, Characters tab"
    say = "Open the Bag and go to the Characters tab."

      [[screen.take]]
      region = "Measure.bagMenuRegion"
      say = "The whole Bag window."

      [[screen.take]]
      images = ["SR.Char.Naruto", "SR.Char.Itadori"]
      in = "Measure.srMenuRegion"
      order = "list"
"""
from __future__ import annotations

import tomllib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

from .common import Item, captured, read_list

ItemKind = Literal["image", "images", "region", "location"]
KINDS: tuple[ItemKind, ...] = ("image", "images", "region", "location")
ITEM_KEYS = {*KINDS, "say", "in", "point", "order"}
SCREEN_KEYS = {"name", "say", "example", "take"}
GUIDE_KEYS = {"title", "say", "screen"}
GROUP = 5  # a converted list merges this many or more images with the same prefix into one `images` item


class GuideError(ValueError):
    """A guide.toml that can't be used; the message says where."""


@dataclass
class Take:
    kind: ItemKind
    names: list[str]  # one name, or many for `images`
    say: str = ""
    within: str | None = None  # `in`: a region target's name
    point: str | list[int] | None = None  # "center" or an offset [dx, dy]
    order: Literal["any", "list"] = "any"


@dataclass
class Screen:
    name: str
    say: str = ""
    example: str | None = None  # a picture of the screen
    take: list[Take] = field(default_factory=list)


@dataclass
class Guide:
    title: str
    say: str = ""
    screens: list[Screen] = field(default_factory=list)


@dataclass(frozen=True)
class Step:
    """One target to take, in order."""

    screen: Screen
    take: Take
    name: str
    index: int  # place among the take's names (for `images`: 3 of 133)

    @property
    def kind(self) -> str:
        """The capture kind: image, region or location."""
        return "image" if self.take.kind == "images" else self.take.kind

    @property
    def item(self) -> Item:
        """As a capture item, for the capture session."""
        return Item(self.name, self.kind, self.take.say, self.screen.name)


@dataclass
class Progress:
    done: int
    total: int
    current: Step | None  # the next thing to take, or None when everything is captured


def _unknown(data: dict, allowed: set[str], where: str) -> None:
    if extra := sorted(set(data) - allowed):
        raise GuideError(f"{where}: unknown key {', '.join(repr(k) for k in extra)}")


def load(path: Path) -> Guide:
    """Read and check a guide.toml. Errors name the screen and item."""
    try:
        data = tomllib.loads(path.read_text(encoding="utf-8"))
    except tomllib.TOMLDecodeError as error:
        raise GuideError(f"{path.name}: {error}") from None
    return parse(data, path.name)


def parse(data: dict, source: str = "guide") -> Guide:
    _unknown(data, GUIDE_KEYS, source)
    guide = Guide(str(data.get("title", "")), str(data.get("say", "")))
    kinds: dict[str, str] = {}
    for s, screen_data in enumerate(data.get("screen", []), 1):
        where = f"{source}, screen {s}"
        _unknown(screen_data, SCREEN_KEYS, where)
        if not screen_data.get("name"):
            raise GuideError(f"{where}: needs a name")
        screen = Screen(screen_data["name"], screen_data.get("say", ""), screen_data.get("example"))
        where = f"{source}, screen {s} ({screen.name})"
        for t, item in enumerate(screen_data.get("take", []), 1):
            here = f"{where}, item {t}"
            _unknown(item, ITEM_KEYS, here)
            given = [k for k in KINDS if k in item]
            if len(given) != 1:
                raise GuideError(f"{here}: needs exactly one of image, images, region, location")
            kind = given[0]
            names = list(item[kind]) if kind == "images" else [item[kind]]
            if not names or not all(isinstance(n, str) and n for n in names):
                raise GuideError(f"{here}: {kind} needs a name")
            order = item.get("order", "any")
            if order not in ("any", "list"):
                raise GuideError(f"{here}: order is \"any\" or \"list\"")
            for name in names:
                if name in kinds:
                    raise GuideError(f"{here}: {name} is in the guide twice")
                kinds[name] = "image" if kind == "images" else kind
            screen.take.append(Take(kind, names, item.get("say", ""), item.get("in"), item.get("point"), order))
        guide.screens.append(screen)
    for screen in guide.screens:
        for take in screen.take:
            if take.within and kinds.get(take.within, "region") != "region":
                raise GuideError(f"{source}, screen ({screen.name}): `in` names {take.within}, which isn't a region")
    return guide


def steps(guide: Guide) -> list[Step]:
    """Every target in the guide, in order."""
    return [Step(screen, take, name, i) for screen in guide.screens for take in screen.take
            for i, name in enumerate(take.names)]


def progress(guide: Guide, images: Path) -> Progress:
    """Done = the target's files exist in `images`. The current step is the first one not done, so an
    `order = "list"` group is taken top to bottom."""
    all_steps = steps(guide)
    left = [s for s in all_steps if not captured(s.item, images)]
    return Progress(len(all_steps) - len(left), len(all_steps), left[0] if left else None)


def _prefix(name: str) -> str:
    return name.rsplit(".", 1)[0] if "." in name else ""


def convert_list(path: Path, title: str = "") -> Guide:
    """An old capture list (capture.txt) as a guide: [headers] become screens, # notes become `say`, and runs
    of 5 or more images with the same prefix (SR.Char.*) become one `images` item in their list order."""
    guide = Guide(title or path.stem)
    for item in read_list(path):
        if not guide.screens or guide.screens[-1].name != (item.screen or "Other"):
            guide.screens.append(Screen(item.screen or "Other"))
        screen = guide.screens[-1]
        screen.take.append(Take(item.kind, [item.name], item.note))  # type: ignore[arg-type]
    for screen in guide.screens:
        merged: list[Take] = []
        for take in screen.take:
            last = merged[-1] if merged else None
            same = last is not None and take.kind == "image" and last.kind in ("image", "images") \
                and _prefix(take.names[0]) and _prefix(take.names[0]) == _prefix(last.names[0])
            if same:
                last.kind, last.order = "images", "list"
                last.names.append(take.names[0])
            else:
                merged.append(take)
        for take in merged:
            if take.kind == "images" and len(take.names) < GROUP:  # too few to group: back to single images
                merged[merged.index(take): merged.index(take) + 1] = [Take("image", [n], take.say) for n in take.names]
            elif take.kind == "images":
                take.say = take.say.split(":")[0].strip()  # "Speed Raid list: Naruto" -> "Speed Raid list"
        screen.take = merged
    return guide


def _q(text: str) -> str:
    return '"' + text.replace("\\", "\\\\").replace('"', '\\"') + '"'


def dump(guide: Guide) -> str:
    """The guide as guide.toml text."""
    out = [f"title = {_q(guide.title)}"]
    if guide.say:
        out.append(f"say = {_q(guide.say)}")
    for screen in guide.screens:
        out += ["", "[[screen]]", f"name = {_q(screen.name)}"]
        if screen.say:
            out.append(f"say = {_q(screen.say)}")
        if screen.example:
            out.append(f"example = {_q(screen.example)}")
        for take in screen.take:
            out += ["", "  [[screen.take]]"]
            if take.kind == "images":
                out.append("  images = [")
                out += [f"    {_q(n)}," for n in take.names]
                out.append("  ]")
            else:
                out.append(f"  {take.kind} = {_q(take.names[0])}")
            if take.within:
                out.append(f"  in = {_q(take.within)}")
            if take.order != "any":
                out.append(f"  order = {_q(take.order)}")
            if take.say:
                out.append(f"  say = {_q(take.say)}")
    return "\n".join(out) + "\n"
