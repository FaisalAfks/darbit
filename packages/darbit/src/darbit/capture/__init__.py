"""Capture tool: take target images, locations and regions from a frozen screen.

One target:
    python -m darbit.capture Gui.Play                 # image: drag a box, Enter saves
    python -m darbit.capture afk/spot --location      # a point
    python -m darbit.capture menus/bag --region       # a region

A session, guided by a card at the top centre of the screen:
    python -m darbit.capture --list capture.txt       # every target in the list not captured yet
    python -m darbit.capture Gui.Play Gui.Bag location:afk/spot region:menus/bag

    A list file has one target per line, a description after "#":
        Gui.Play                     # lobby: the Play button
        location: afk/spot           # AFK: where to click to stay active
        region: menus/bag            # the bag window

    Get the screen ready and press F8: the screen freezes for the current target.
    The card hides when the mouse is away and comes back when it's near the top
    centre. "+ Add" adds a target (and writes it to the list). Undo takes back the
    last capture; Done (or Ctrl+Alt+Q) keeps or deletes this session's captures.

A setup guide (guide.toml, see capture/guide.py) walks through screens in order:
    python -m darbit.capture --guide guide.toml      # every target in the guide not captured yet
    python -m darbit.capture --guide capture.txt     # convert a list into guide.toml next to it, once

Targets are saved in the `images` folder next to the list, guide or script, or in
`images` here for names on the command line; --folder changes it.
"""

import argparse
import gc
import time
import tkinter as tk
from pathlib import Path

from ..platform import screen
from . import guide
from .common import Item, Result, captured, distinct, parse_item, read_list
from .overlay import Overlay
from .session import HOTKEYS, Session
from .store import save_result

screen.enable_dpi_awareness()

__all__ = ["Item", "distinct", "main", "read_list"]


def _single(item: Item, folder: Path, delay: float) -> int:
    for left in range(int(delay), 0, -1):
        print(f"freezing in {left}...", flush=True)
        time.sleep(1)
    time.sleep(delay - int(delay))
    shot, origin = screen.grab()
    root = tk.Tk()
    root.withdraw()
    outcome: list[Result | None] = []

    def done(action: str, result: Result | None) -> None:
        outcome.append(result if action == "save" else None)
        root.destroy()

    Overlay(root, shot, origin, item.kind, item.name, done)
    root.mainloop()
    if not outcome or outcome[0] is None:
        print("cancelled")
        return 1
    print(save_result(folder, item, outcome[0], shot, origin, None).message)
    return 0


def main(argv: list[str] | None = None) -> int:
    # Tk objects must be freed on Tk's own thread. With automatic collection off,
    # garbage is only collected here, on the main thread, between steps and at the end.
    gc.disable()
    try:
        return _main(argv)
    finally:
        gc.collect()


def _main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m darbit.capture", description="Capture targets from the screen.")
    parser.add_argument("names", nargs="*", help="target names, e.g. Gui.Play, location:afk/spot, region:menus/bag")
    parser.add_argument("--list", dest="list_file", help="a list file of targets to capture")
    parser.add_argument("--guide", dest="guide_file", help="a setup guide (guide.toml), or a list to convert into one")
    parser.add_argument("--folder", help="where to save (default: images next to the list or guide)")
    parser.add_argument("--all", action="store_true", help="session: include targets already captured")
    parser.add_argument("--location", action="store_true", help="one target: a point instead of an image")
    parser.add_argument("--region", action="store_true", help="one target: a region instead of an image")
    parser.add_argument("--delay", type=float, default=3, help="one target: seconds before the screen freezes")
    parser.add_argument("--hotkey", default="f8", choices=sorted(HOTKEYS), help="session: the capture key")
    parser.add_argument("--window", help="session: window to save the size of, e.g. Roblox")
    args = parser.parse_args(argv)

    if args.guide_file and Path(args.guide_file).suffix == ".txt":
        return _convert(Path(args.guide_file))

    list_file = Path(args.list_file).resolve() if args.list_file else None
    guide_file = Path(args.guide_file).resolve() if args.guide_file else None
    home = list_file or guide_file
    folder = Path(args.folder) if args.folder else (home.parent / "images" if home else Path("images"))

    items = [parse_item(n) for n in args.names]
    if list_file:
        if not list_file.is_file():
            list_file.write_text("", encoding="utf-8")
        items += read_list(list_file)
    if guide_file:
        try:
            for step in guide.steps(guide.load(guide_file)):
                items.append(step.item)
        except (OSError, guide.GuideError) as error:
            print(error)
            return 2
    if home and not args.all:
        items = [i for i in items if not captured(i, folder)]
    seen: set[tuple[str, str]] = set()
    items = [i for i in items if (i.name, i.kind) not in seen and not seen.add((i.name, i.kind))]

    if not home:
        if not items:
            print("give a target name or --list capture.txt")
            return 2
        if len(items) == 1:
            kind = "location" if args.location else "region" if args.region else items[0].kind
            return _single(Item(items[0].name, kind), folder, args.delay)
    print(
        f"{len(items)} to capture into {folder}; press {args.hotkey.upper()} when each is on screen, "
        "Ctrl+Alt+Q to finish"
    )
    Session(items, folder, args.hotkey, args.window, list_file).run()
    return 0


def _convert(list_file: Path) -> int:
    """Write guide.toml next to an old capture list."""
    out = list_file.with_name("guide.toml")
    if out.exists():
        print(f"{out} already exists; delete it first to convert again")
        return 2
    out.write_text(guide.dump(guide.convert_list(list_file)), encoding="utf-8", newline="\n")
    print(f"wrote {out}: check each screen's `say`, then capture with --guide {out.name}")
    return 0
