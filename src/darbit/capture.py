"""Capture tool: take target images, locations and regions from a frozen screen.

One target:
    python -m darbit.capture Gui.Play                 # image: drag a box, Enter saves
    python -m darbit.capture afk/spot --location      # a point
    python -m darbit.capture menus/bag --region       # a region

A session, guided by a small window at the top of the screen:
    python -m darbit.capture --from bot.py            # every image bot.py uses that isn't captured yet
    python -m darbit.capture Gui.Play Gui.Bag location:afk/spot region:menus/bag

    In the session, get the screen ready and press F8: the screen freezes for the
    next target. After saving, the window moves on to the next one.

On the frozen screen:
    drag            the image (green), or the region in region mode
    R, then drag    the image's search region (red); without one it searches the whole screen
    C, then click   the click point (cross); without one it clicks the centre
    arrows          move the box 1 pixel; Shift+arrows resize it
    Enter           save        Esc     cancel

The bar at the top shows the mouse position and the boxes in screen pixels.
"""
from __future__ import annotations

import argparse
import base64
import ctypes
import re
import sys
import time
import tkinter as tk
import tokenize
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

import cv2
import numpy as np

from .core import matching
from .core.geometry import Location, Region
from .core.targets import find_file, save
from .platform import screen

screen.enable_dpi_awareness()

ZOOM, ZOOM_SIZE = 8, 21  # magnifier: 21x21 pixels shown 8 times bigger
HOTKEYS = {"f8": 0x77, "f9": 0x78, "f10": 0x79}


@dataclass(frozen=True)
class Item:
    """One thing to capture: kind is "image", "location" or "region"."""

    name: str
    kind: str = "image"

    @staticmethod
    def parse(text: str) -> Item:
        kind, _, name = text.partition(":")
        if name and kind in ("image", "location", "region"):
            return Item(name, kind)
        return Item(text)


@dataclass
class Result:
    image: Region | None = None
    region: Region | None = None
    point: Location | None = None


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


def images_in(script: Path) -> list[str]:
    """Every image name written in a script (strings ending in .png, comments ignored), in order."""
    names: list[str] = []
    with script.open(encoding="utf-8") as file:
        for token in tokenize.generate_tokens(file.readline):
            if token.type == tokenize.STRING:
                for name in re.findall(r"[^\"']+\.png", token.string):
                    if name not in names:
                        names.append(name)
    return names


# ------------------------------------------------------------------ frozen screen


class Overlay:
    """The frozen screen. Calls `done(result)` on Enter, or `done(None)` on Esc."""

    def __init__(self, root: tk.Tk, shot: np.ndarray, origin: Region, kind: str, title: str,
                 done: Callable[[Result | None], None]) -> None:
        self.shot, self.origin, self.kind, self.title, self.done = shot, origin, kind, title, done
        self.result = Result()
        self.mode = {"image": "image", "location": "point", "region": "region"}[kind]
        self._start: tuple[int, int] | None = None
        self.mouse = (origin.x, origin.y)

        self.window = tk.Toplevel(root)
        self.window.overrideredirect(True)
        self.window.geometry(f"{origin.w}x{origin.h}+{origin.x}+{origin.y}")
        self.window.attributes("-topmost", True)
        self.canvas = tk.Canvas(self.window, width=origin.w, height=origin.h, highlightthickness=0,
                                cursor="crosshair")
        self.canvas.pack()
        self.photo = _photo(shot)
        self.canvas.create_image(0, 0, anchor="nw", image=self.photo)
        self.bar_back = self.canvas.create_rectangle(0, 0, 0, 0, fill="black", outline="")
        self.bar = self.canvas.create_text(10, 8, anchor="nw", fill="white", font=("Consolas", 12))
        self.zoom_photo: tk.PhotoImage | None = None
        self.zoom = self.canvas.create_image(0, 0, anchor="nw")

        self.canvas.bind("<ButtonPress-1>", self._down)
        self.canvas.bind("<B1-Motion>", self._drag)
        self.canvas.bind("<ButtonRelease-1>", self._up)
        self.canvas.bind("<Motion>", self._move)
        w = self.window
        w.bind("<Escape>", lambda _e: self._close(None))
        w.bind("<Return>", lambda _e: self._finish())
        if kind == "image":
            w.bind("<KeyPress-r>", lambda _e: self._set_mode("region"))
            w.bind("<KeyPress-c>", lambda _e: self._set_mode("point"))
            w.bind("<KeyPress-i>", lambda _e: self._set_mode("image"))
        for key, (dx, dy) in {"Left": (-1, 0), "Right": (1, 0), "Up": (0, -1), "Down": (0, 1)}.items():
            w.bind(f"<KeyPress-{key}>", lambda _e, dx=dx, dy=dy: self._nudge(dx, dy, False))
            w.bind(f"<Shift-KeyPress-{key}>", lambda _e, dx=dx, dy=dy: self._nudge(dx, dy, True))
        self._draw()
        w.after(50, w.focus_force)

    # ----------------------------------------------------------------- input

    def _screen(self, x: int, y: int) -> tuple[int, int]:
        return x + self.origin.x, y + self.origin.y

    def _set_mode(self, mode: str) -> None:
        self.mode = mode
        self._draw()

    def _down(self, event: tk.Event) -> None:
        self._start = (event.x, event.y)
        if self.mode == "point":
            self.result.point = Location(*self._screen(event.x, event.y))
            self._draw()

    def _drag(self, event: tk.Event) -> None:
        self._move(event)
        if self._start is None or self.mode == "point":
            return
        x0, y0 = self._start
        box = Region(*self._screen(min(x0, event.x), min(y0, event.y)), abs(event.x - x0), abs(event.y - y0))
        if self.mode == "image":
            self.result.image = box
        else:
            self.result.region = box
        self._draw()

    def _up(self, event: tk.Event) -> None:
        self._drag(event)
        self._start = None
        if self.kind == "image" and self.mode != "image":
            self.mode = "image"
        self._draw()

    def _move(self, event: tk.Event) -> None:
        self.mouse = self._screen(event.x, event.y)
        self._draw_zoom(event.x, event.y)
        self._draw_bar()

    def _nudge(self, dx: int, dy: int, resize: bool) -> None:
        """Arrows move the current box (or point) 1 pixel; Shift+arrows grow or shrink its right and bottom edges."""
        if self.mode == "point":
            if self.result.point:
                self.result.point = self.result.point.moved(dx, dy)
        else:
            box = self.result.image if self.mode == "image" else self.result.region
            if box is None:
                return
            box = Region(box.x, box.y, max(1, box.w + dx), max(1, box.h + dy)) if resize else box.moved(dx, dy)
            if self.mode == "image":
                self.result.image = box
            else:
                self.result.region = box
        self._draw()

    def _finish(self) -> None:
        r = self.result
        if self.kind == "location" and r.point is None:
            return
        if self.kind == "region" and (r.region is None or r.region.w < 3 or r.region.h < 3):
            return
        if self.kind == "image" and (r.image is None or r.image.w < 3 or r.image.h < 3):
            return
        self._close(r)

    def _close(self, result: Result | None) -> None:
        self.window.destroy()
        self.done(result)

    # ------------------------------------------------------------------ draw

    def _box(self, box: Region, color: str) -> None:
        x, y = box.x - self.origin.x, box.y - self.origin.y
        self.canvas.create_rectangle(x, y, x + box.w, y + box.h, outline=color, width=2, tags="marks")

    def _draw(self) -> None:
        self.canvas.delete("marks")
        r = self.result
        if r.region:
            self._box(r.region, "red")
        if r.image:
            self._box(r.image, "lime")
        point = r.point or (r.image.center if r.image else None)
        if point:
            x, y = point.x - self.origin.x, point.y - self.origin.y
            self.canvas.create_line(x - 10, y, x + 11, y, fill="cyan", width=2, tags="marks")
            self.canvas.create_line(x, y - 10, x, y + 11, fill="cyan", width=2, tags="marks")
        self._draw_bar()

    def _draw_zoom(self, x: int, y: int) -> None:
        half = ZOOM_SIZE // 2
        h, w = self.shot.shape[:2]
        crop = np.zeros((ZOOM_SIZE, ZOOM_SIZE, 3), np.uint8)
        x0, y0 = x - half, y - half
        sx0, sy0, sx1, sy1 = max(0, x0), max(0, y0), min(w, x0 + ZOOM_SIZE), min(h, y0 + ZOOM_SIZE)
        if sx1 > sx0 and sy1 > sy0:
            crop[sy0 - y0 : sy1 - y0, sx0 - x0 : sx1 - x0] = self.shot[sy0:sy1, sx0:sx1]
        big = cv2.resize(crop, None, fx=ZOOM, fy=ZOOM, interpolation=cv2.INTER_NEAREST)
        c = half * ZOOM
        cv2.rectangle(big, (c, c), (c + ZOOM - 1, c + ZOOM - 1), (255, 255, 0), 1)
        cv2.rectangle(big, (0, 0), (big.shape[1] - 1, big.shape[0] - 1), (255, 255, 255), 1)
        self.zoom_photo = _photo(big)
        size = big.shape[0]
        zx = x + 24 if x + 24 + size < self.origin.w else x - 24 - size
        zy = y + 24 if y + 24 + size < self.origin.h else y - 24 - size
        self.canvas.itemconfigure(self.zoom, image=self.zoom_photo)
        self.canvas.coords(self.zoom, zx, zy)
        self.canvas.tag_raise(self.zoom)

    def _draw_bar(self) -> None:
        def fmt(r: Region | None) -> str:
            return f"{r.x},{r.y},{r.w},{r.h}" if r else "-"

        r = self.result
        point = f"{round(r.point.x)},{round(r.point.y)}" if r.point else "-"
        keys = {"image": "drag image, R region, C click point", "location": "click a point",
                "region": "drag a region"}[self.kind]
        text = (f"{self.title}  [{self.mode}]  mouse {self.mouse[0]},{self.mouse[1]}  image {fmt(r.image)}  "
                f"region {fmt(r.region)}  point {point}  | {keys}, arrows nudge, Enter save, Esc cancel")
        self.canvas.itemconfigure(self.bar, text=text)
        x0, y0, x1, y1 = self.canvas.bbox(self.bar)
        self.canvas.coords(self.bar_back, x0 - 6, y0 - 4, x1 + 6, y1 + 4)
        self.canvas.tag_raise(self.bar_back)
        self.canvas.tag_raise(self.bar)


# ------------------------------------------------------------------ saving


def save_result(folder: Path, item: Item, result: Result, shot: np.ndarray, origin: Region,
                window: list[int] | None) -> str:
    """Save a captured target and say what was saved."""
    path = folder / item.name
    if item.kind == "location":
        p = result.point
        save(path, None, location=[round(p.x), round(p.y)], window=window)
        return f"saved {path}.json: location {round(p.x)},{round(p.y)}"
    if item.kind == "region":
        r = result.region
        save(path, None, region=[r.x, r.y, r.w, r.h], window=window)
        return f"saved {path}.json: region {r.x},{r.y},{r.w},{r.h}"
    box = result.image
    image = shot[box.y - origin.y : box.bottom - origin.y, box.x - origin.x : box.right - origin.x].copy()
    offset = None
    if result.point is not None:
        center = box.center
        offset = [round(result.point.x - center.x), round(result.point.y - center.y)]
    region = [result.region.x, result.region.y, result.region.w, result.region.h] if result.region else None
    save(path, image, region=region, offset=offset, scale=screen.scale_at(box.x, box.y), window=window)
    elsewhere = distinct(image, shot, Region(box.x - origin.x, box.y - origin.y, box.w, box.h))
    verdict = "distinct" if elsewhere < 0.7 else "RISKY, something else looks alike"
    return (f"saved {path}.png ({box.w}x{box.h} at {box.x},{box.y})"
            + (f", region {region}" if region else "") + (f", click offset {offset}" if offset else "")
            + f"; {verdict} (best elsewhere {elsewhere:.2f})")


def _window_size(name: str | None) -> list[int] | None:
    if not name:
        return None
    from .runtime import apps
    area = apps.window(name)
    return [area.w, area.h] if area else None


# ------------------------------------------------------------------ session


class Session:
    """A small window at the top centre that walks through targets; the hotkey captures the current one."""

    WIDTH, HEIGHT = 460, 118
    BACK, FRONT, DIM, ACCENT = "#1e1f24", "#f2f2f2", "#9a9ca5", "#4cc2ff"

    def __init__(self, items: list[Item], folder: Path, hotkey: str, window: str | None) -> None:
        self.items, self.folder, self.window_name = items, folder, window
        self.index = 0
        self.vk = HOTKEYS[hotkey]
        self.hotkey = hotkey.upper()
        self.capturing = False
        self._was_down = False

        self.root = tk.Tk()
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)
        self.root.configure(bg=self.BACK)
        desk = screen.monitors()[0] if screen.monitors() else screen.desktop()
        self.x = desk.x + (desk.w - self.WIDTH) // 2
        self.top = desk.y + 16
        self.y = desk.y - self.HEIGHT
        self.root.geometry(f"{self.WIDTH}x{self.HEIGHT}+{self.x}+{self.y}")

        frame = tk.Frame(self.root, bg=self.BACK, padx=16, pady=10)
        frame.pack(fill="both", expand=True)
        self.count = tk.Label(frame, bg=self.BACK, fg=self.DIM, font=("Segoe UI", 9))
        self.count.pack(anchor="w")
        self.name = tk.Label(frame, bg=self.BACK, fg=self.FRONT, font=("Segoe UI Semibold", 15))
        self.name.pack(anchor="w")
        self.hint = tk.Label(frame, bg=self.BACK, fg=self.ACCENT, font=("Segoe UI", 10))
        self.hint.pack(anchor="w")
        buttons = tk.Frame(frame, bg=self.BACK)
        buttons.pack(anchor="e", fill="x", pady=(4, 0))
        self.status = tk.Label(buttons, bg=self.BACK, fg=self.DIM, font=("Segoe UI", 9))
        self.status.pack(side="left")
        for text, action in (("Quit", self.root.destroy), ("Skip", self._skip), ("Back", self._back)):
            tk.Button(buttons, text=text, command=action, bg="#2d2f36", fg=self.FRONT, relief="flat",
                      activebackground="#3a3d46", activeforeground=self.FRONT, padx=10).pack(side="right", padx=3)

        self._show()
        self._slide_in()
        self._poll()

    # ------------------------------------------------------------ animation

    def _slide_in(self) -> None:
        if self.y < self.top:
            self.y = min(self.top, self.y + max(2, (self.top - self.y) // 4))
            self.root.geometry(f"+{self.x}+{self.y}")
            self.root.after(12, self._slide_in)

    def _pulse(self, step: int = 0) -> None:
        colors = ["#4cc2ff", "#7dd3ff", "#a9e2ff", "#7dd3ff", "#4cc2ff"]
        if step < len(colors):
            self.name.configure(fg=colors[step])
            self.root.after(60, lambda: self._pulse(step + 1))
        else:
            self.name.configure(fg=self.FRONT)

    # -------------------------------------------------------------- content

    def _show(self) -> None:
        if self.index >= len(self.items):
            self.count.configure(text=f"{len(self.items)} of {len(self.items)}")
            self.name.configure(text="All done")
            self.hint.configure(text="Close with Quit")
            return
        item = self.items[self.index]
        what = {"image": "Box the image", "location": "Click the point", "region": "Box the region"}[item.kind]
        self.count.configure(text=f"{self.index + 1} of {len(self.items)}  ·  {item.kind}")
        self.name.configure(text=item.name)
        self.hint.configure(text=f"Get it on screen, then press {self.hotkey}. {what}, Enter to save.")
        self._pulse()

    def _skip(self) -> None:
        if self.index < len(self.items):
            self.index += 1
            self.status.configure(text="skipped")
            self._show()

    def _back(self) -> None:
        if self.index > 0:
            self.index -= 1
            self.status.configure(text="")
            self._show()

    # -------------------------------------------------------------- capture

    def _poll(self) -> None:
        down = bool(ctypes.windll.user32.GetAsyncKeyState(self.vk) & 0x8000)
        if down and not self._was_down and not self.capturing and self.index < len(self.items):
            self._capture()
        self._was_down = down
        self.root.after(30, self._poll)

    def _capture(self) -> None:
        self.capturing = True
        self.root.withdraw()
        self.root.update()
        time.sleep(0.15)  # let the window disappear before the shot
        shot, origin = screen.grab()
        item = self.items[self.index]

        def done(result: Result | None) -> None:
            self.capturing = False
            self.root.deiconify()
            self.root.attributes("-topmost", True)
            if result is None:
                self.status.configure(text="cancelled")
                return
            message = save_result(self.folder, item, result, shot, origin, _window_size(self.window_name))
            print(message, flush=True)
            self.status.configure(text="RISKY match, check it" if "RISKY" in message else "saved")
            self.index += 1
            self._show()

        Overlay(self.root, shot, origin, item.kind, f"{item.name} ({item.kind})", done)

    def run(self) -> None:
        self.root.mainloop()


# ------------------------------------------------------------------ command


def _single(item: Item, folder: Path, delay: float, window: str | None) -> int:
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
    print(save_result(folder, item, outcome[0], shot, origin, _window_size(window)))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m darbit.capture", description="Capture targets from the screen.")
    parser.add_argument("names", nargs="*", help="target names, e.g. Gui.Play, location:afk/spot, region:menus/bag")
    parser.add_argument("--from", dest="script", help="capture every image this script uses that isn't saved yet")
    parser.add_argument("--folder", default="images", help="where to save (default: images)")
    parser.add_argument("--location", action="store_true", help="one target: a point instead of an image")
    parser.add_argument("--region", action="store_true", help="one target: a region instead of an image")
    parser.add_argument("--delay", type=float, default=3, help="one target: seconds before the screen freezes")
    parser.add_argument("--hotkey", default="f8", choices=sorted(HOTKEYS), help="session: the capture key")
    parser.add_argument("--window", help="window to save the size of, e.g. Roblox")
    args = parser.parse_args(argv)
    folder = Path(args.folder)

    items = [Item.parse(n) for n in args.names]
    if args.script:
        items += [Item(n.removesuffix(".png")) for n in images_in(Path(args.script))
                  if find_file(n, [folder]) is None]
    if not items:
        print("nothing to capture" if args.script else "give a target name, or --from script.py")
        return 0 if args.script else 2
    if len(items) == 1 and not args.script:
        kind = "location" if args.location else "region" if args.region else items[0].kind
        return _single(Item(items[0].name, kind), folder, args.delay, args.window)
    print(f"{len(items)} to capture; press {args.hotkey.upper()} when each is on screen")
    Session(items, folder, args.hotkey, args.window).run()
    return 0


if __name__ == "__main__":
    sys.exit(main())
