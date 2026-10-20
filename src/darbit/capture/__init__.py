"""Capture tool: take target images, locations and regions from a frozen screen.

One target:
    python -m darbit.capture Gui.Play                 # image: drag a box, Enter saves
    python -m darbit.capture afk/spot --location      # a point
    python -m darbit.capture menus/bag --region       # a region

A session, guided by a card at the top centre of the screen:
    python -m darbit.capture --from bot.py            # every image bot.py uses that isn't captured yet
    python -m darbit.capture --reference ../old-images   # every hand-named image in an old folder
    python -m darbit.capture Gui.Play Gui.Bag location:afk/spot region:menus/bag

    Get the screen ready and press F8: the screen freezes for the current target.
    The card hides when the mouse is away and comes back when it's near the top
    centre. Undo takes back the last capture; Done (or Ctrl+Alt+Q) keeps or deletes
    this session's captures.
"""
from __future__ import annotations

import argparse
import time
import tkinter as tk
from pathlib import Path

from ..core.targets import find_file
from ..platform import screen
from .common import Item, Result, distinct, images_in, reference_names
from .overlay import Overlay
from .session import HOTKEYS, Session
from .store import save_result

screen.enable_dpi_awareness()

__all__ = ["Item", "distinct", "images_in", "main"]


def _single(item: Item, folder: Path, delay: float) -> int:
    for left in range(int(delay), 0, -1):
        print(f"freezing in {left}...", flush=True)
        time.sleep(1)
    time.sleep(delay - int(delay))
    shot, origin = screen.grab()
    root = tk.Tk()
    root.withdraw()
    outcome: list[Result | None] = []

    def done(result: Result | None) -> None:
        outcome.append(result)
        root.destroy()

    Overlay(root, shot, origin, item.kind, item.name, done)
    root.mainloop()
    if not outcome or outcome[0] is None:
        print("cancelled")
        return 1
    print(save_result(folder, item, outcome[0], shot, origin, None).message)
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m darbit.capture", description="Capture targets from the screen.")
    parser.add_argument("names", nargs="*", help="target names, e.g. Gui.Play, location:afk/spot, region:menus/bag")
    parser.add_argument("--from", dest="script", help="capture every image this script uses that isn't saved yet")
    parser.add_argument("--reference", help="capture every image named by hand in this old folder (numbered "
                        "and (Old) files skipped), showing the old image while capturing")
    parser.add_argument("--folder", default="images", help="where to save (default: images)")
    parser.add_argument("--location", action="store_true", help="one target: a point instead of an image")
    parser.add_argument("--region", action="store_true", help="one target: a region instead of an image")
    parser.add_argument("--delay", type=float, default=3, help="one target: seconds before the screen freezes")
    parser.add_argument("--hotkey", default="f8", choices=sorted(HOTKEYS), help="session: the capture key")
    parser.add_argument("--window", help="session: window to save the size of, e.g. Roblox")
    args = parser.parse_args(argv)
    folder = Path(args.folder)

    items = [Item.parse(n) for n in args.names]
    if args.script:
        items += [Item(n.removesuffix(".png")) for n in images_in(Path(args.script))
                  if find_file(n, [folder]) is None]
    if args.reference:
        named = [i for i in reference_names(Path(args.reference)) if find_file(i.name, [folder]) is None]
        named.sort(key=lambda i: i.name.startswith("SR.Char."))  # the long Speed Raid list last
        items += named
    if not items:
        print("nothing to capture" if args.script or args.reference else "give a target name, or --from script.py")
        return 0 if args.script or args.reference else 2
    if len(items) == 1 and not (args.script or args.reference):
        kind = "location" if args.location else "region" if args.region else items[0].kind
        return _single(Item(items[0].name, kind), folder, args.delay)
    print(f"{len(items)} to capture; press {args.hotkey.upper()} when each is on screen, Ctrl+Alt+Q to finish")
    Session(items, folder, args.hotkey, args.window).run()
    return 0
