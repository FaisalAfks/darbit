"""Capture tool: take target images, locations and regions from a frozen screen.

    python -m darbit.capture Gui.Play                 # drag a box around the image, Enter saves
    python -m darbit.capture afk/spot --location      # click a point, Enter saves
    python -m darbit.capture --folder images --delay 5 Gui.Bag

On the frozen screen:
    drag            the image (green)
    R, then drag    its search region (red); without one it searches the whole screen
    C, then click   its click point (cross); without one it clicks the centre
    Enter           save        Esc     cancel

The bar at the top shows the mouse position and the boxes in screen pixels, so it
also works for measuring Locations and Regions to put in a script.
"""
from __future__ import annotations

import argparse
import base64
import sys
import time
import tkinter as tk
from pathlib import Path
from tkinter import simpledialog

import cv2
import numpy as np

from .core import matching
from .core.geometry import Location, Region
from .core.targets import save
from .platform import screen

screen.enable_dpi_awareness()


def _photo(pixels: np.ndarray) -> tk.PhotoImage:
    _, data = cv2.imencode(".png", pixels)
    return tk.PhotoImage(data=base64.b64encode(data.tobytes()))


def distinct(image: np.ndarray, shot: np.ndarray, box: Region) -> float:
    """The best score the image gets anywhere other than where it was taken: lower is safer."""
    result = matching.scores(image, shot)
    if result is None:
        return 0.0
    h, w = image.shape[:2]
    result[max(0, box.y - h + 1) : box.y + h, max(0, box.x - w + 1) : box.x + w] = -1
    return float(result.max()) if result.size else 0.0


class Capture:
    def __init__(self, shot: np.ndarray, origin: Region, location_only: bool) -> None:
        self.shot, self.origin, self.location_only = shot, origin, location_only
        self.image: Region | None = None
        self.region: Region | None = None
        self.point: Location | None = None
        self.mode = "point" if location_only else "image"
        self.saved = False
        self._start: tuple[int, int] | None = None

        self.root = tk.Tk()
        self.root.overrideredirect(True)
        self.root.geometry(f"{origin.w}x{origin.h}+{origin.x}+{origin.y}")
        self.root.attributes("-topmost", True)
        self.canvas = tk.Canvas(self.root, width=origin.w, height=origin.h, highlightthickness=0, cursor="crosshair")
        self.canvas.pack()
        self.photo = _photo(shot)
        self.canvas.create_image(0, 0, anchor="nw", image=self.photo)
        self.bar = self.canvas.create_text(10, 8, anchor="nw", fill="white", font=("Consolas", 12))
        self.bar_back = self.canvas.create_rectangle(0, 0, 0, 0, fill="black", outline="")
        self.canvas.tag_lower(self.bar_back, self.bar)
        self.mouse = (0, 0)

        self.canvas.bind("<ButtonPress-1>", self._down)
        self.canvas.bind("<B1-Motion>", self._drag)
        self.canvas.bind("<ButtonRelease-1>", self._up)
        self.canvas.bind("<Motion>", self._move)
        self.root.bind("<Escape>", lambda _e: self.root.destroy())
        self.root.bind("<Return>", lambda _e: self._finish())
        self.root.bind("<KeyPress-r>", lambda _e: self._set_mode("region"))
        self.root.bind("<KeyPress-c>", lambda _e: self._set_mode("point"))
        self.root.bind("<KeyPress-i>", lambda _e: self._set_mode("image"))
        self._draw()
        self.root.focus_force()

    def _screen(self, x: int, y: int) -> tuple[int, int]:
        return x + self.origin.x, y + self.origin.y

    def _set_mode(self, mode: str) -> None:
        if not (self.location_only and mode != "point"):
            self.mode = mode
            self._draw()

    def _down(self, event: tk.Event) -> None:
        self._start = (event.x, event.y)
        if self.mode == "point":
            self.point = Location(*self._screen(event.x, event.y))
            self._draw()

    def _drag(self, event: tk.Event) -> None:
        self._move(event)
        if self._start is None or self.mode == "point":
            return
        x0, y0 = self._start
        box = Region(*self._screen(min(x0, event.x), min(y0, event.y)), abs(event.x - x0), abs(event.y - y0))
        if self.mode == "image":
            self.image = box
        else:
            self.region = box
        self._draw()

    def _up(self, event: tk.Event) -> None:
        self._drag(event)
        self._start = None
        if self.mode == "region" and not self.location_only:
            self.mode = "image"
        self._draw()

    def _move(self, event: tk.Event) -> None:
        self.mouse = self._screen(event.x, event.y)
        self._draw_bar()

    def _box(self, box: Region, color: str, tag: str) -> None:
        x, y = box.x - self.origin.x, box.y - self.origin.y
        self.canvas.create_rectangle(x, y, x + box.w, y + box.h, outline=color, width=2, tags=tag)

    def _draw(self) -> None:
        self.canvas.delete("marks")
        if self.region:
            self._box(self.region, "red", "marks")
        if self.image:
            self._box(self.image, "lime", "marks")
        point = self.point or (self.image.center if self.image else None)
        if point:
            x, y = point.x - self.origin.x, point.y - self.origin.y
            self.canvas.create_line(x - 10, y, x + 11, y, fill="cyan", width=2, tags="marks")
            self.canvas.create_line(x, y - 10, x, y + 11, fill="cyan", width=2, tags="marks")
        self._draw_bar()

    def _draw_bar(self) -> None:
        def fmt(r: Region | None) -> str:
            return f"{r.x},{r.y},{r.w},{r.h}" if r else "-"

        if self.location_only:
            text = (f"mouse {self.mouse[0]},{self.mouse[1]}   point "
                    f"{f'{round(self.point.x)},{round(self.point.y)}' if self.point else '-'}"
                    "   | click a point, Enter save, Esc cancel")
        else:
            text = (f"[{self.mode}] mouse {self.mouse[0]},{self.mouse[1]}   image {fmt(self.image)}   "
                    f"region {fmt(self.region)}   | drag image, R region, C click point, Enter save, Esc cancel")
        self.canvas.itemconfigure(self.bar, text=text)
        x0, y0, x1, y1 = self.canvas.bbox(self.bar)
        self.canvas.coords(self.bar_back, x0 - 6, y0 - 4, x1 + 6, y1 + 4)
        self.canvas.tag_raise(self.bar_back)
        self.canvas.tag_raise(self.bar)

    def _finish(self) -> None:
        if self.location_only and self.point is None:
            return
        if not self.location_only and (self.image is None or self.image.w < 3 or self.image.h < 3):
            return
        self.saved = True
        self.root.destroy()

    def run(self) -> bool:
        self.root.mainloop()
        return self.saved


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m darbit.capture", description="Capture a target from the screen.")
    parser.add_argument("name", nargs="?", help="target name, e.g. Gui.Play or lobby/play")
    parser.add_argument("--folder", default="images", help="where to save (default: images)")
    parser.add_argument("--delay", type=float, default=3, help="seconds before the screen freezes (default: 3)")
    parser.add_argument("--location", action="store_true", help="capture a point instead of an image")
    parser.add_argument("--window", help="window to save the size of, e.g. Roblox")
    args = parser.parse_args(argv)

    for left in range(int(args.delay), 0, -1):
        print(f"freezing in {left}...", flush=True)
        time.sleep(1)
    time.sleep(args.delay - int(args.delay))
    shot, origin = screen.grab()

    tool = Capture(shot, origin, args.location)
    if not tool.run():
        print("cancelled")
        return 1

    name = args.name
    if not name:
        root = tk.Tk()
        root.withdraw()
        name = simpledialog.askstring("darbit", "Target name (e.g. Gui.Play):")
        root.destroy()
        if not name:
            print("cancelled")
            return 1

    window = None
    if args.window:
        from .runtime import apps
        area = apps.window(args.window)
        window = [area.w, area.h] if area else None

    path = Path(args.folder) / name
    point = tool.point
    if args.location:
        save(path, None, location=[round(point.x), round(point.y)], window=window)
        print(f"saved {path}.json: location {round(point.x)},{round(point.y)}")
        return 0

    box = tool.image
    image = shot[box.y - origin.y : box.bottom - origin.y, box.x - origin.x : box.right - origin.x].copy()
    offset = None
    if point is not None:
        center = box.center
        offset = [round(point.x - center.x), round(point.y - center.y)]
    region = [tool.region.x, tool.region.y, tool.region.w, tool.region.h] if tool.region else None
    scale = screen.scale_at(box.x, box.y)
    save(path, image, region=region, offset=offset, scale=scale, window=window)

    elsewhere = distinct(image, shot, Region(box.x - origin.x, box.y - origin.y, box.w, box.h))
    verdict = "distinct" if elsewhere < 0.7 else "RISKY: something else looks alike"
    print(f"saved {path}.png ({box.w}x{box.h} at {box.x},{box.y})"
          + (f", region {region}" if region else "") + (f", click offset {offset}" if offset else ""))
    print(f"{verdict}: best score elsewhere on screen {elsewhere:.2f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
