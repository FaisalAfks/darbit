"""The frozen screen where a target is boxed or pointed at.

    drag            the image (green), the region, or the point, depending on the kind
    R, then drag    the image's search region (red)
    C, then click   the image's click point (cross)
    arrows          move the box 1 pixel; Shift+arrows resize it
    Enter           save        Esc     cancel
"""
from __future__ import annotations

import tkinter as tk
from collections.abc import Callable

import cv2
import numpy as np

from ..core.geometry import Location, Region
from .common import Result, Theme, photo, rounded

ZOOM, ZOOM_SIZE = 8, 21  # magnifier: 21x21 pixels shown 8 times bigger
DIM = 0.42  # how bright the screen is outside the box


class Overlay:
    """Calls `done(result)` on Enter, or `done(None)` on Esc."""

    def __init__(self, root: tk.Tk, shot: np.ndarray, origin: Region, kind: str, title: str,
                 done: Callable[[Result | None], None]) -> None:
        self.shot, self.origin, self.kind, self.title, self.done = shot, origin, kind, title, done
        self.result = Result()
        self.mode = {"image": "image", "location": "point", "region": "region"}[kind]
        self._start: tuple[int, int] | None = None
        self._bright_due = False
        self.mouse = (origin.x, origin.y)

        self.window = tk.Toplevel(root)
        self.window.overrideredirect(True)
        self.window.geometry(f"{origin.w}x{origin.h}+{origin.x}+{origin.y}")
        self.window.attributes("-topmost", True)
        c = self.canvas = tk.Canvas(self.window, width=origin.w, height=origin.h, highlightthickness=0,
                                    cursor="crosshair", bg="black")
        c.pack()
        self.dim_photo = photo((shot * DIM).astype(np.uint8))
        c.create_image(0, 0, anchor="nw", image=self.dim_photo)
        self.bright_photo: tk.PhotoImage | None = None
        self.bright = c.create_image(0, 0, anchor="nw")
        self.zoom_photo: tk.PhotoImage | None = None
        self.zoom = c.create_image(0, 0, anchor="nw")

        c.bind("<ButtonPress-1>", self._down)
        c.bind("<B1-Motion>", self._drag)
        c.bind("<ButtonRelease-1>", self._up)
        c.bind("<Motion>", self._move)
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
        ready = {"location": r.point is not None,
                 "region": r.region is not None and r.region.w >= 3 and r.region.h >= 3,
                 "image": r.image is not None and r.image.w >= 3 and r.image.h >= 3}[self.kind]
        if ready:
            self._close(r)

    def _close(self, result: Result | None) -> None:
        self.window.destroy()
        self.done(result)

    # ------------------------------------------------------------------ draw

    def _local(self, box: Region) -> tuple[int, int, int, int]:
        x, y = box.x - self.origin.x, box.y - self.origin.y
        return x, y, x + box.w, y + box.h

    def _schedule_bright(self) -> None:
        # re-cutting the bright part on every mouse move is slow for big boxes; do it at most every 40 ms
        if not self._bright_due:
            self._bright_due = True
            self.window.after(40, self._draw_bright)

    def _draw_bright(self) -> None:
        self._bright_due = False
        box = self.result.image if self.kind == "image" else self.result.region
        if box is None or box.w < 1 or box.h < 1:
            self.canvas.itemconfigure(self.bright, image="")
            return
        x0, y0, x1, y1 = self._local(box)
        x0, y0 = max(0, x0), max(0, y0)
        crop = self.shot[y0:y1, x0:x1]
        if crop.size == 0:
            return
        self.bright_photo = photo(crop)
        self.canvas.itemconfigure(self.bright, image=self.bright_photo)
        self.canvas.coords(self.bright, x0, y0)

    def _draw(self) -> None:
        c = self.canvas
        c.delete("marks")
        r = self.result
        self._schedule_bright()
        if r.region:
            x0, y0, x1, y1 = self._local(r.region)
            c.create_rectangle(x0, y0, x1, y1, outline=Theme.DANGER, width=2, dash=(6, 4), tags="marks")
            c.create_text(x0 + 4, y0 - 4, anchor="sw", text="search region", fill=Theme.DANGER,
                          font=(Theme.FONT, 9), tags="marks")
        if r.image:
            x0, y0, x1, y1 = self._local(r.image)
            c.create_rectangle(x0, y0, x1, y1, outline=Theme.OK, width=2, tags="marks")
            c.create_text(x0, y1 + 4, anchor="nw", text=f"{r.image.w} × {r.image.h}", fill=Theme.OK,
                          font=(Theme.MONO, 9), tags="marks")
        point = r.point or (r.image.center if r.image else None)
        if point:
            x, y = point.x - self.origin.x, point.y - self.origin.y
            c.create_oval(x - 7, y - 7, x + 7, y + 7, outline=Theme.ACCENT, width=2, tags="marks")
            c.create_line(x - 12, y, x + 13, y, fill=Theme.ACCENT, width=1, tags="marks")
            c.create_line(x, y - 12, x, y + 13, fill=Theme.ACCENT, width=1, tags="marks")
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
        cv2.rectangle(big, (c - 1, c - 1), (c + ZOOM, c + ZOOM), (250, 200, 90), 1)
        self.zoom_photo = photo(big)
        size = big.shape[0]
        zx = x + 28 if x + 28 + size < self.origin.w else x - 28 - size
        zy = y + 28 if y + 28 + size + 22 < self.origin.h else y - 28 - size - 22
        canvas = self.canvas
        canvas.delete("zoom")
        rounded(canvas, zx - 3, zy - 3, zx + size + 3, zy + size + 25, 8, fill=Theme.CARD, outline=Theme.LINE,
                tags="zoom")
        canvas.itemconfigure(self.zoom, image=self.zoom_photo)
        canvas.coords(self.zoom, zx, zy)
        canvas.create_text(zx + size / 2, zy + size + 11, text=f"{self.mouse[0]}, {self.mouse[1]}",
                           fill=Theme.TEXT, font=(Theme.MONO, 9), tags="zoom")
        canvas.tag_raise("zoom")
        canvas.tag_raise(self.zoom)

    def _draw_bar(self) -> None:
        c = self.canvas
        c.delete("bar")
        hints = {"image": "drag  image     R  region     C  click point",
                 "location": "click  point", "region": "drag  region"}[self.kind]
        parts = [(self.title, Theme.TEXT, (Theme.BOLD, 11)),
                 (f"  {self.mode}  ", Theme.KIND_COLOR.get(self.kind, Theme.ACCENT), (Theme.FONT, 10)),
                 (f"{hints}     arrows  nudge     Enter  save     Esc  cancel", Theme.MUTED, (Theme.FONT, 10))]
        x, y = 0, self.origin.h - 34
        ids = []
        for text, color, font in parts:
            item = c.create_text(x, y, anchor="w", text=text, fill=color, font=font, tags="bar")
            ids.append(item)
            x = c.bbox(item)[2]
        shift = (self.origin.w - x) / 2
        for item in ids:
            c.move(item, shift, 0)
        x0, y0, x1, y1 = c.bbox("bar")
        back = rounded(c, x0 - 18, y0 - 9, x1 + 18, y1 + 9, 16, fill=Theme.CARD, outline=Theme.LINE, tags="bar")
        c.tag_lower(back, ids[0])
