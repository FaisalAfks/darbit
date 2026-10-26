"""Setup guides: an ordered walk-through of what to capture for a bot. See docs/tasks/T12-setup-guide.md.

A guide.toml lists screens, and on each screen the targets to take, in order. `load` reads and checks
it, `steps` lists every target in order, `progress` says how many are captured and what's next, and
`convert_list` turns an old capture list (capture.txt) into a guide that `dump` writes out.
"""

import tomllib
from dataclasses import dataclass, field
from pathlib import Path

from .common import Item, captured, read_list

KINDS = ("image", "images", "region", "location")
ITEM_KEYS = {"image", "images", "region", "location", "say", "in", "point", "order"}
SCREEN_KEYS = {"name", "say", "example", "take"}
GUIDE_KEYS = {"title", "say", "screen"}
GROUP = 5  # a converted list merges a run of this many images with the same prefix into one `images` item


class GuideError(ValueError):
    """A guide.toml that can't be used; the message says where."""


@dataclass
class Take:
    """One item on a screen: a target, or for `images` several of one kind."""

    kind: str  # image, images, region or location
    names: list[str]  # one name, or many for `images`
    say: str = ""
    within: str | None = None  # `in`: the name of a region target
    point: str | list[int] | None = None  # "center" or an offset [dx, dy]
    order: str = "any"  # "list": taken strictly in the order given


@dataclass
class Screen:
    name: str
    say: str = ""
    example: str | None = None  # a picture of what the screen looks like
    take: list[Take] = field(default_factory=list)


@dataclass
class Guide:
    title: str
    say: str = ""
    screens: list[Screen] = field(default_factory=list)


@dataclass
class Step:
    """One target to take, with the screen and item it belongs to."""

    screen: Screen
    take: Take
    name: str
    index: int  # its place among the item's names (for `images`: 3 of 133)

    @property
    def kind(self) -> str:
        """The capture kind: image, region or location."""
        if self.take.kind == "images":
            return "image"
        return self.take.kind

    @property
    def item(self) -> Item:
        """The step as a capture item, for the capture session."""
        return Item(self.name, self.kind, self.take.say, self.screen.name)


@dataclass
class Progress:
    done: int
    total: int
    current: Step | None  # the next target to take, or None when everything is captured


def load(path: Path) -> Guide:
    """Read and check a guide.toml. Errors name the screen and item."""
    try:
        data = tomllib.loads(path.read_text(encoding="utf-8"))
    except tomllib.TOMLDecodeError as error:
        raise GuideError(f"{path.name}: {error}") from None
    return parse(data, path.name)


def parse(data: dict, source: str = "guide") -> Guide:
    """A guide from already-read TOML data. `source` names it in errors."""
    _check_keys(data, GUIDE_KEYS, source)
    guide = Guide(str(data.get("title", "")), str(data.get("say", "")))
    kinds: dict[str, str] = {}  # every target's capture kind, to find duplicates and check `in`
    for number, screen_data in enumerate(data.get("screen", []), start=1):
        screen = _parse_screen(screen_data, f"{source}, screen {number}", kinds)
        guide.screens.append(screen)
    for screen in guide.screens:
        for take in screen.take:
            _check_within(take, kinds, f"{source}, screen ({screen.name})")
    return guide


def _parse_screen(data: dict, where: str, kinds: dict[str, str]) -> Screen:
    _check_keys(data, SCREEN_KEYS, where)
    if not data.get("name"):
        raise GuideError(f"{where}: needs a name")
    screen = Screen(data["name"], data.get("say", ""), data.get("example"))
    for number, item_data in enumerate(data.get("take", []), start=1):
        take = _parse_take(item_data, f"{where} ({screen.name}), item {number}", kinds)
        screen.take.append(take)
    return screen


def _parse_take(data: dict, where: str, kinds: dict[str, str]) -> Take:
    _check_keys(data, ITEM_KEYS, where)
    given = []
    for kind in KINDS:
        if kind in data:
            given.append(kind)
    if len(given) != 1:
        raise GuideError(f"{where}: needs exactly one of image, images, region, location")
    kind = given[0]

    if kind == "images":
        names = data[kind]
    else:
        names = [data[kind]]
    if not isinstance(names, list) or not names:
        raise GuideError(f"{where}: {kind} needs a name")
    for name in names:
        if not isinstance(name, str) or not name:
            raise GuideError(f"{where}: {kind} needs a name")
        if name in kinds:
            raise GuideError(f"{where}: {name} is in the guide twice")
        if kind == "images":
            kinds[name] = "image"
        else:
            kinds[name] = kind

    order = data.get("order", "any")
    if order not in ("any", "list"):
        raise GuideError(f'{where}: order is "any" or "list"')
    return Take(kind, list(names), data.get("say", ""), data.get("in"), data.get("point"), order)


def _check_keys(data: dict, allowed: set[str], where: str) -> None:
    unknown = []
    for key in data:
        if key not in allowed:
            unknown.append(repr(key))
    if unknown:
        raise GuideError(f"{where}: unknown key {', '.join(sorted(unknown))}")


def _check_within(take: Take, kinds: dict[str, str], where: str) -> None:
    # `in` may name a region taken elsewhere (not in this guide); only a target of another kind is wrong
    if take.within is None:
        return
    kind = kinds.get(take.within, "region")
    if kind != "region":
        raise GuideError(f"{where}: `in` names {take.within}, which isn't a region")


def steps(guide: Guide) -> list[Step]:
    """Every target in the guide, in order."""
    found = []
    for screen in guide.screens:
        for take in screen.take:
            for index, name in enumerate(take.names):
                found.append(Step(screen, take, name, index))
    return found


def progress(guide: Guide, images: Path) -> Progress:
    """How many targets are saved in `images`, and the first one that isn't.

    The first missing step is next, so an `order = "list"` item is taken top to bottom.
    """
    all_steps = steps(guide)
    left = []
    for step in all_steps:
        if not captured(step.item, images):
            left.append(step)
    current = None
    if left:
        current = left[0]
    return Progress(len(all_steps) - len(left), len(all_steps), current)


def convert_list(path: Path, title: str = "") -> Guide:
    """An old capture list as a guide.

    `[headers]` become screens and `#` notes become `say`. A run of 5 or more images with the same
    prefix (`SR.Char.*`) whose notes only repeat their names becomes one `images` item, kept in the
    list's order.
    """
    guide = Guide(title or path.stem)
    for item in read_list(path):
        screen_name = item.screen or "Other"
        if not guide.screens or guide.screens[-1].name != screen_name:
            guide.screens.append(Screen(screen_name))
        guide.screens[-1].take.append(Take(item.kind, [item.name], item.note))
    for screen in guide.screens:
        screen.take = _group_images(screen.take)
    return guide


def _prefix(name: str) -> str:
    """`SR.Char.Naruto` -> `SR.Char`; a name without a dot has none."""
    if "." not in name:
        return ""
    return name.rsplit(".", 1)[0]


def _group_images(takes: list[Take]) -> list[Take]:
    # first collect runs of images with the same prefix, then keep only the long runs as `images`
    runs: list[list[Take]] = []
    for take in takes:
        prefix = _prefix(take.names[0])
        joins = False
        if runs and take.kind == "image" and prefix != "":
            first = runs[-1][0]
            joins = first.kind == "image" and prefix == _prefix(first.names[0])
        if joins:
            runs[-1].append(take)
        else:
            runs.append([take])

    grouped = []
    for run in runs:
        if len(run) < GROUP or not _notes_only_repeat_names(run):
            grouped += run
            continue
        names = []
        for take in run:
            names.append(take.names[0])
        say = run[0].say.split(":")[0].strip()  # "Speed Raid list: Naruto" -> "Speed Raid list"
        grouped.append(Take("images", names, say, order="list"))
    return grouped


def _notes_only_repeat_names(run: list[Take]) -> bool:
    """Whether every note is `<where>: <the name's last part>`, so one `say` for the group loses nothing.

    "Speed Raid list: Naruto" for SR.Char.Naruto repeats the name; "Play menu: Raid Challenge" for
    Play.DailyRaid says something the name doesn't.
    """
    for take in run:
        if not take.say:
            continue
        where, _, what = take.say.partition(":")
        last_part = take.names[0].rsplit(".", 1)[-1]
        if not where or what.strip() != last_part:
            return False
    return True


def dump(guide: Guide) -> str:
    """The guide as guide.toml text."""
    lines = [f"title = {_quote(guide.title)}"]
    if guide.say:
        lines.append(f"say = {_quote(guide.say)}")
    for screen in guide.screens:
        lines += ["", "[[screen]]", f"name = {_quote(screen.name)}"]
        if screen.say:
            lines.append(f"say = {_quote(screen.say)}")
        if screen.example:
            lines.append(f"example = {_quote(screen.example)}")
        for take in screen.take:
            lines += ["", "  [[screen.take]]"]
            lines += _dump_take(take)
    return "\n".join(lines) + "\n"


def _dump_take(take: Take) -> list[str]:
    lines = []
    if take.kind == "images":
        lines.append("  images = [")
        for name in take.names:
            lines.append(f"    {_quote(name)},")
        lines.append("  ]")
    else:
        lines.append(f"  {take.kind} = {_quote(take.names[0])}")
    if take.within:
        lines.append(f"  in = {_quote(take.within)}")
    if take.point == "center":
        lines.append('  point = "center"')
    elif take.point:
        lines.append(f"  point = [{take.point[0]}, {take.point[1]}]")
    if take.order != "any":
        lines.append(f"  order = {_quote(take.order)}")
    if take.say:
        lines.append(f"  say = {_quote(take.say)}")
    return lines


def _quote(text: str) -> str:
    """A TOML basic string."""
    return '"' + text.replace("\\", "\\\\").replace('"', '\\"') + '"'
