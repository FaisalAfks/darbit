"""Capture tool: take target images, locations and regions from a frozen screen.

One target:
    python -m darbit.capture Gui.Play                 # image: drag a box, Enter saves
    python -m darbit.capture afk/spot --location      # a point
    python -m darbit.capture menus/bag --region       # a region

A session, guided by a card at the top centre of the screen:
    python -m darbit.capture --list capture.txt       # every target in the list not captured yet
    python -m darbit.capture --list capture.txt --harvest "Speed Raid characters"   # a scrolling grid
    python -m darbit.capture --from bot.py            # every image bot.py uses that isn't captured yet
    python -m darbit.capture Gui.Play Gui.Bag location:afk/spot region:menus/bag

    A list file has one target per line, a description after "#":
        Gui.Play                     # lobby: the Play button
        location: afk/spot           # AFK: where to click to stay active
        region: menus/bag            # the bag window

    Get the screen ready and press F8: the screen freezes for the current target.
    The card hides when the mouse is away and comes back when it's near the top
    centre. "+ Add" adds a target (and writes it to the list). Undo takes back the
    last capture; Done (or Ctrl+Alt+Q) keeps or deletes this session's captures.

Targets are saved in the `images` folder next to the list or script, or in
`images` here for names on the command line; --folder changes it.
"""
from __future__ import annotations

import argparse
import gc
import time
import tkinter as tk
from pathlib import Path

from ..platform import screen
from .common import Item, Result, captured, distinct, images_in, read_list
from .overlay import Overlay
from .session import HOTKEYS, Session
from .store import save_result

screen.enable_dpi_awareness()

__all__ = ["Item", "distinct", "images_in", "main", "read_list"]


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
    parser.add_argument("--harvest", metavar="GROUP", help="harvest a scrolling grid into the list's [GROUP] targets")
    parser.add_argument("--from", dest="script", help="capture every image this script uses that isn't saved yet")
    parser.add_argument("--folder", help="where to save (default: images next to the list or script)")
    parser.add_argument("--all", action="store_true", help="session: include targets already captured")
    parser.add_argument("--location", action="store_true", help="one target: a point instead of an image")
    parser.add_argument("--region", action="store_true", help="one target: a region instead of an image")
    parser.add_argument("--delay", type=float, default=3, help="one target: seconds before the screen freezes")
    parser.add_argument("--hotkey", default="f8", choices=sorted(HOTKEYS), help="session: the capture key")
    parser.add_argument("--window", help="session: window to save the size of, e.g. Roblox")
    args = parser.parse_args(argv)

    list_file = Path(args.list_file).resolve() if args.list_file else None
    script = Path(args.script).resolve() if args.script else None
    home = list_file or script
    folder = Path(args.folder) if args.folder else (home.parent / "images" if home else Path("images"))

    items = [Item.parse(n) for n in args.names]
    if list_file:
        if not list_file.is_file():
            list_file.write_text("", encoding="utf-8")
        items += read_list(list_file)
    if script:
        items += [Item(n.removesuffix(".png")) for n in images_in(script)]
    if home and not args.all:
        items = [i for i in items if not captured(i, folder)]
    seen: set[tuple[str, str]] = set()
    items = [i for i in items if (i.name, i.kind) not in seen and not seen.add((i.name, i.kind))]

    if args.harvest:
        group = [i for i in items if i.screen == args.harvest]
        if not group:
            print(f"no targets left in [{args.harvest}]")
            return 0
        from .harvest import run
        print(f"{len(group)} names in [{args.harvest}]; saving into {folder}")
        return run(group, folder, args.delay)
    if not home:
        if not items:
            print("give a target name, --list capture.txt or --from script.py")
            return 2
        if len(items) == 1:
            kind = "location" if args.location else "region" if args.region else items[0].kind
            return _single(Item(items[0].name, kind), folder, args.delay)
    print(f"{len(items)} to capture into {folder}; press {args.hotkey.upper()} when each is on screen, "
          "Ctrl+Alt+Q to finish")
    Session(items, folder, args.hotkey, args.window, list_file).run()
    return 0
