"""Harvest a scrolling grid of items (a character list, a rewards page) into one image per cell.

    python -m darbit.capture --list capture.txt --harvest "Speed Raid characters"

1. The screen freezes. Box the first cell, then the cell diagonally next to it
   (right and down), then the list area.
2. Every whole cell is cut out. The list scrolls with the mouse wheel and the cut
   repeats, until no new cells show up.
3. A review screen shows every cell with a name from the list's group, in order.
   Click a cell to rename it; right-click to leave it out. Save writes the images.
"""
from __future__ import annotations

import os
import time
import tkinter as tk
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

import cv2
import numpy as np

from ..core.geometry import Region
from ..platform import screen
from .common import Item, Result, Theme, photo, rounded
from .overlay import Overlay
from .store import Saved, save_result

SAME = 0.97  # cells scoring this alike are the same item
MAX_SCROLLS = 80


@dataclass(frozen=True)
class Grid:
    first: Region  # the first cell, on screen
    dx: int  # from one column to the next
    dy: int  # from one row to the next
    area: Region  # the visible list


def cells(grid: Grid, top: float) -> list[Region]:
    """Every whole cell inside the list area, row by row, with the first row's top at `top`."""
    size_w, size_h = grid.first.w, grid.first.h
    area = grid.area
    xs = []
    x = grid.first.x
    while x - grid.dx >= area.x:
        x -= grid.dx
    while x + size_w <= area.right:
        xs.append(x)
        x += grid.dx
    y = top
    while y - grid.dy >= area.y:
        y -= grid.dy
    found = []
    while y + size_h <= area.bottom:
        if y >= area.y:
            found.extend(Region(int(x), round(y), size_w, size_h) for x in xs)
        y += grid.dy
    return found


def moved(before: np.ndarray, after: np.ndarray, area: Region, origin: Region, dy: int) -> int:
    """How many pixels the list scrolled up between two shots (0 if it didn't move)."""
    x0, y0 = area.x - origin.x, area.y - origin.y
    old = before[y0 : y0 + area.h, x0 : x0 + area.w]
    new = after[y0 : y0 + area.h, x0 : x0 + area.w]
    band_h = min(dy, area.h // 3)
    band_top = area.h // 2 - band_h // 2
    band = old[band_top : band_top + band_h]
    result = cv2.matchTemplate(new, band, cv2.TM_CCOEFF_NORMED)
    _, score, _, (_, y) = cv2.minMaxLoc(result)
    return band_top - y if score > 0.8 else 0


def alike(a: np.ndarray, b: np.ndarray) -> bool:
    if a.shape != b.shape:
        return False
    return float(cv2.matchTemplate(a, b, cv2.TM_CCOEFF_NORMED)[0, 0]) >= SAME


def harvest(grid: Grid, grab: Callable[[], tuple[np.ndarray, Region]], scroll: Callable[[], None],
            progress: Callable[[int], None] = lambda _n: None) -> list[np.ndarray]:
    """Cut every cell of the list, scrolling until nothing new shows. Cells come back in list order."""
    shot, origin = grab()
    top = float(grid.first.y)
    found: list[np.ndarray] = []

    def take(image: np.ndarray, top: float) -> int:
        new = 0
        for cell in cells(grid, top):
            x, y = cell.x - origin.x, cell.y - origin.y
            piece = image[y : y + cell.h, x : x + cell.w].copy()
            if not any(alike(piece, seen) for seen in found[-60:]):
                found.append(piece)
                new += 1
        return new

    take(shot, top)
    progress(len(found))
    for _ in range(MAX_SCROLLS):
        scroll()
        time.sleep(0.35)
        after, origin = grab()
        shift = moved(shot, after, grid.area, origin, grid.dy)
        if shift == 0:
            break
        top -= shift
        new = take(after, top)
        progress(len(found))
        shot = after
        if new == 0:
            break
    return found


# ------------------------------------------------------------------ the steps on screen


class Harvest:
    """Grid setup on the frozen screen, the harvest itself, then the review."""

    def __init__(self, items: list[Item], folder: Path) -> None:
        self.items, self.folder = items, folder
        self.root = tk.Tk()
        self.root.withdraw()
        self.boxes: list[Region] = []
        self.cells: list[np.ndarray] = []
        self.saved: list[Saved] = []

    def run(self) -> list[Saved]:
        self.shot, self.origin = screen.grab()
        self._step()
        self.root.mainloop()
        return self.saved

    def _step(self) -> None:
        titles = ["Harvest 1/3: box the first cell", "Harvest 2/3: box the next cell diagonally (right and down)",
                  "Harvest 3/3: box the list area"]
        kinds = ["image", "image", "region"]
        n = len(self.boxes)
        Overlay(self.root, self.shot, self.origin, kinds[n], titles[n], self._boxed)

    def _boxed(self, action: str, result: Result | None) -> None:
        if action != "save" or result is None:
            self.root.destroy()
            return
        self.boxes.append(result.image or result.region)
        if len(self.boxes) < 3:
            self._step()
            return
        first, second, area = self.boxes
        grid = Grid(first, second.x - first.x, second.y - first.y, area)
        if grid.dx <= 0 or grid.dy <= 0:
            print("the second cell must be right of and below the first")
            self.root.destroy()
            return
        print("harvesting; keep the mouse still", flush=True)
        from ..platform import input as device

        center = area.center.point()

        def scroll() -> None:
            device.move(*center, 0.2)
            device.scroll(-3)

        self.cells = harvest(grid, screen.grab, scroll, lambda n: print(f"  {n} cells", flush=True))
        Review(self).show()


class Review:
    """Every harvested cell with its name; fix names, then save."""

    COLUMNS, THUMB = 10, 92

    def __init__(self, harvest: Harvest) -> None:
        self.h = harvest
        self.names = [item.name for item in harvest.items[: len(harvest.cells)]]
        self.names += [""] * (len(harvest.cells) - len(self.names))
        common = os.path.commonprefix([n for n in self.names if n])
        self.prefix = common[: common.rfind(".") + 1] if "." in common else ""  # e.g. "SR.Char.", hidden in labels
        self.skipped: set[int] = set()
        self.selected: int | None = None
        self._images: list[tk.PhotoImage] = []

    def show(self) -> None:
        root = self.h.root
        self.window = tk.Toplevel(root)
        self.window.title("Harvest review")
        self.window.configure(bg=Theme.CARD)
        self.window.protocol("WM_DELETE_WINDOW", root.destroy)
        top = tk.Frame(self.window, bg=Theme.CARD, padx=16, pady=12)
        top.pack(fill="x")
        count = len(self.h.cells)
        tk.Label(top, text=f"{count} cells, {len(self.h.items)} names in the list", bg=Theme.CARD, fg=Theme.TEXT,
                 font=(Theme.BOLD, 13)).pack(side="left")
        tk.Button(top, text="Save", command=self._save, bg=Theme.ACCENT, fg="#0b1220", relief="flat",
                  font=(Theme.BOLD, 11), padx=16).pack(side="right")
        tk.Button(top, text="Cancel", command=root.destroy, bg=Theme.RAISED, fg=Theme.TEXT, relief="flat",
                  font=(Theme.BOLD, 11), padx=16).pack(side="right", padx=8)
        edit = tk.Frame(self.window, bg=Theme.CARD, padx=16)
        edit.pack(fill="x")
        tk.Label(edit, text="Name of the selected cell:", bg=Theme.CARD, fg=Theme.MUTED,
                 font=(Theme.FONT, 10)).pack(side="left")
        self.entry = tk.Entry(edit, bg=Theme.RAISED, fg=Theme.TEXT, insertbackground=Theme.TEXT, relief="flat",
                              font=(Theme.FONT, 12), width=40)
        self.entry.pack(side="left", padx=8)
        self.entry.bind("<Return>", lambda _e: self._rename())
        tk.Label(edit, text="click a cell to pick it, right-click to leave it out", bg=Theme.CARD, fg=Theme.MUTED,
                 font=(Theme.FONT, 10)).pack(side="left", padx=8)

        rows = (count + self.COLUMNS - 1) // self.COLUMNS
        cell_w, cell_h = self.THUMB + 48, self.THUMB + 40
        frame = tk.Frame(self.window, bg=Theme.CARD)
        frame.pack(fill="both", expand=True)
        self.canvas = tk.Canvas(frame, bg=Theme.CARD, highlightthickness=0, width=self.COLUMNS * cell_w + 16,
                                height=min(rows * cell_h + 16, 900), scrollregion=(0, 0, 0, rows * cell_h + 16))
        bar = tk.Scrollbar(frame, command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=bar.set)
        self.canvas.pack(side="left", fill="both", expand=True)
        bar.pack(side="right", fill="y")
        self.canvas.bind_all("<MouseWheel>", lambda e: self.canvas.yview_scroll(-e.delta // 120, "units"))
        self._draw()

    def _draw(self) -> None:
        c = self.canvas
        c.delete("all")
        self._images.clear()
        cell_w, cell_h = self.THUMB + 48, self.THUMB + 40
        for i, image in enumerate(self.h.cells):
            col, row = i % self.COLUMNS, i // self.COLUMNS
            x0, y0 = 8 + col * cell_w, 8 + row * cell_h
            skipped = i in self.skipped
            outline = Theme.ACCENT if i == self.selected else (Theme.DANGER if skipped else Theme.LINE)
            tag = f"cell-{i}"
            rounded(c, x0, y0, x0 + cell_w - 8, y0 + cell_h - 8, 10, fill=Theme.RAISED, outline=outline, width=2,
                    tags=tag)
            ih, iw = image.shape[:2]
            scale = min(self.THUMB / iw, self.THUMB / ih)
            thumb = photo(cv2.resize(image, (max(1, round(iw * scale)), max(1, round(ih * scale)))))
            self._images.append(thumb)
            c.create_image(x0 + (cell_w - 8) / 2, y0 + 6 + self.THUMB / 2, image=thumb, tags=tag)
            name = "left out" if skipped else (self.names[i].removeprefix(self.prefix) or "no name")
            short = name if len(name) <= 15 else name[:14] + "…"
            c.create_text(x0 + (cell_w - 8) / 2, y0 + self.THUMB + 18, text=short,
                          fill=Theme.MUTED if skipped or not self.names[i] else Theme.TEXT, font=(Theme.FONT, 9),
                          tags=tag)
            c.tag_bind(tag, "<Button-1>", lambda _e, i=i: self._select(i))
            c.tag_bind(tag, "<Button-3>", lambda _e, i=i: self._toggle(i))

    def _select(self, i: int) -> None:
        self.selected = i
        self.entry.delete(0, "end")
        self.entry.insert(0, self.names[i])
        self.entry.focus_set()
        self._draw()

    def _toggle(self, i: int) -> None:
        self.skipped ^= {i}
        self._draw()

    def _rename(self) -> None:
        if self.selected is not None:
            self.names[self.selected] = self.entry.get().strip().removesuffix(".png")
            nxt = self.selected + 1
            if nxt < len(self.names):
                self._select(nxt)
            else:
                self._draw()

    def _save(self) -> None:
        count = 0
        for i, image in enumerate(self.h.cells):
            name = self.names[i]
            if i in self.skipped or not name:
                continue
            h, w = image.shape[:2]
            result = Result(image=Region(0, 0, w, h))
            saved = save_result(self.h.folder, Item(name), result, image, Region(0, 0, w, h), None)
            self.h.saved.append(saved)
            count += 1
        print(f"saved {count} cells into {self.h.folder}", flush=True)
        self.h.root.destroy()


def run(items: list[Item], folder: Path, delay: float = 3) -> int:
    for left in range(int(delay), 0, -1):
        print(f"freezing in {left}...", flush=True)
        time.sleep(1)
    Harvest(items, folder).run()
    return 0
