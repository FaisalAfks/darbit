"""The frozen screen where a target is boxed or pointed at.

    drag            box the image (green), or the region; edges snap to lines nearby (hold Alt to stop)
    click           box the element under the mouse, found from its edges
    R, then drag    the image's search region (red)
    C, then click   the image's click point (cross)
    arrows          move the box 1 pixel; Shift+arrows resize it

    Enter           save            Tab        skip
    Space           take a new shot  Backspace  undo the last capture
    Esc             back to the card
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
SNAP = 6  # pixels within which an edge pulls the box edge to it
CLICK = 4  # a press and release closer than this is a click, not a drag
ALT = 0x20000  # Tk's Alt modifier on Windows

Done = Callable[[str, Result | None], None]  # action: save, cancel, refreeze, skip, undo


def edges_of(shot: np.ndarray) -> np.ndarray:
    gray = cv2.cvtColor(shot, cv2.COLOR_BGR2GRAY)
    return cv2.Canny(gray, 60, 160)


def snap(edges: np.ndarray, x: int, y: int, reach: int = SNAP) -> tuple[int, int]:
    """Move a point onto the strongest vertical and horizontal line within `reach` pixels, if there is one."""
    h, w = edges.shape
    span = 4 * reach  # how far along a line to look: far enough to see a line that starts at a corner
    x0, x1 = max(0, x - reach), min(w, x + reach + 1)
    y0, y1 = max(0, y - reach), min(h, y + reach + 1)
    columns = (edges[max(0, y - span) : min(h, y + span + 1), x0:x1] > 0).sum(axis=0)
    rows = (edges[y0:y1, max(0, x - span) : min(w, x + span + 1)] > 0).sum(axis=1)
    if columns.size and columns.max() >= reach:
        x = x0 + int(columns.argmax())
    if rows.size and rows.max() >= reach:
        y = y0 + int(rows.argmax())
    return x, y


def _fill(shot: np.ndarray, x: int, y: int, diff: int = 12) -> Region:
    """The area of similar colour connected to (x, y)."""
    h, w = shot.shape[:2]
    mask = np.zeros((h + 2, w + 2), np.uint8)
    cv2.floodFill(shot, mask, (x, y), 0, (diff,) * 3, (diff,) * 3, 4 | cv2.FLOODFILL_MASK_ONLY | (255 << 8))
    ys, xs = np.nonzero(mask[1:-1, 1:-1])
    return Region(int(xs.min()), int(ys.min()), int(xs.max() - xs.min() + 1), int(ys.max() - ys.min() + 1))


def box_at(shot: np.ndarray, x: int, y: int) -> Region | None:
    """The button or icon that was clicked.

    Fills outward from the click by colour: clicking a button's background gives the
    whole button. A small fill (a letter on the button) keeps growing to the area just
    outside it while that stays button-sized; a huge fill (the background around an
    icon) falls back to the shape's edges.
    """
    h, w = shot.shape[:2]
    found = _fill(shot, x, y)
    if found.w * found.h > 0.2 * w * h:
        return _shape_at(shot, x, y)
    if found.w >= 40 and found.h >= 30:
        return found
    grown = None
    for _ in range(4):
        step = _grow(shot, grown or found, x, y)
        if step is None:
            break
        grown = step
    return grown or _shape_at(shot, x, y) or found


def _grow(shot: np.ndarray, inner: Region, x: int, y: int) -> Region | None:
    """The biggest button-sized area of one colour just outside `inner` that contains it."""
    h, w = shot.shape[:2]
    best = None
    for px, py in ((inner.x - 3, y), (inner.right + 2, y), (x, inner.y - 3), (x, inner.bottom + 2)):
        if not (0 <= px < w and 0 <= py < h):
            continue
        around = _fill(shot, px, py)
        inside = around.x <= inner.x and around.y <= inner.y and around.right >= inner.right \
            and around.bottom >= inner.bottom
        bigger = around.w * around.h > inner.w * inner.h
        button_sized = around.w * around.h <= 0.06 * w * h
        if inside and bigger and button_sized and (best is None or around.w * around.h > best.w * best.h):
            best = around
    return best


def _shape_at(shot: np.ndarray, x: int, y: int, around: tuple[int, int] = (900, 600)) -> Region | None:
    """The smallest closed shape around (x, y), from the edges near it."""
    h, w = shot.shape[:2]
    left, top = max(0, x - around[0] // 2), max(0, y - around[1] // 2)
    right, bottom = min(w, left + around[0]), min(h, top + around[1])
    edges = edges_of(shot[top:bottom, left:right])
    edges = cv2.dilate(edges, np.ones((3, 3), np.uint8))
    contours, _ = cv2.findContours(edges, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
    px, py = x - left, y - top
    best = None
    limit = 0.7 * (right - left) * (bottom - top)
    for contour in contours:
        bx, by, bw, bh = cv2.boundingRect(contour)
        if bw < 12 or bh < 12 or bw * bh > limit:
            continue
        if bx <= px < bx + bw and by <= py < by + bh and (best is None or bw * bh < best[2] * best[3]):
            best = (bx, by, bw, bh)
    if best is None:
        return None
    bx, by, bw, bh = best
    return Region(left + bx, top + by, bw, bh)


class Overlay:
    def __init__(self, root: tk.Tk, shot: np.ndarray, origin: Region, kind: str, title: str, done: Done,
                 counter: str = "", message: str = "") -> None:
        self.shot, self.origin, self.kind, self.title, self.done = shot, origin, kind, title, done
        self.counter, self.message = counter, message
        self.result = Result()
        self.mode = {"image": "image", "location": "point", "region": "region"}[kind]
        self._start: tuple[int, int] | None = None
        self._bright_due = False
        self._edges: np.ndarray | None = None
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
        w.bind("<Escape>", lambda _e: self._close("cancel", None))
        w.bind("<Return>", lambda _e: self._finish())
        w.bind("<space>", lambda _e: self._close("refreeze", None))
        w.bind("<Tab>", lambda _e: self._close("skip", None))
        w.bind("<BackSpace>", lambda _e: self._close("undo", None))
        if kind == "image":
            w.bind("<KeyPress-r>", lambda _e: self._set_mode("region"))
            w.bind("<KeyPress-c>", lambda _e: self._set_mode("point"))
            w.bind("<KeyPress-i>", lambda _e: self._set_mode("image"))
        for key, (dx, dy) in {"Left": (-1, 0), "Right": (1, 0), "Up": (0, -1), "Down": (0, 1)}.items():
            w.bind(f"<KeyPress-{key}>", lambda _e, dx=dx, dy=dy: self._nudge(dx, dy, False))
            w.bind(f"<Shift-KeyPress-{key}>", lambda _e, dx=dx, dy=dy: self._nudge(dx, dy, True))
        self._draw()
        w.after(50, w.focus_force)

    @property
    def edges(self) -> np.ndarray:
        if self._edges is None:
            self._edges = edges_of(self.shot)
        return self._edges

    # ----------------------------------------------------------------- input

    def _screen(self, x: int, y: int) -> tuple[int, int]:
        return x + self.origin.x, y + self.origin.y

    def _snapped(self, event: tk.Event) -> tuple[int, int]:
        if event.state & ALT or self.mode == "point":
            return event.x, event.y
        return snap(self.edges, event.x, event.y)

    def _set_mode(self, mode: str) -> None:
        self.mode = mode
        self._draw()

    def _down(self, event: tk.Event) -> None:
        self._start = self._snapped(event)
        self._pressed_at = (event.x, event.y)
        if self.mode == "point":
            self.result.point = Location(*self._screen(event.x, event.y))
            self._draw()

    def _drag(self, event: tk.Event) -> None:
        self._move(event)
        if self._start is None or self.mode == "point":
            return
        if abs(event.x - self._pressed_at[0]) < CLICK and abs(event.y - self._pressed_at[1]) < CLICK:
            return
        x0, y0 = self._start
        x1, y1 = self._snapped(event)
        box = Region(*self._screen(min(x0, x1), min(y0, y1)), abs(x1 - x0), abs(y1 - y0))
        self._set_box(box)

    def _up(self, event: tk.Event) -> None:
        if self._start is not None and self.mode != "point":
            moved = abs(event.x - self._pressed_at[0]) >= CLICK or abs(event.y - self._pressed_at[1]) >= CLICK
            if moved:
                self._drag(event)
            else:
                found = box_at(self.shot, event.x, event.y)
                if found is None:
                    self.message = "no shape found there; drag a box instead"
                else:
                    self._set_box(found.moved(self.origin.x, self.origin.y))
                    self.message = ""
        self._start = None
        if self.kind == "image" and self.mode != "image":
            self.mode = "image"
        self._draw()

    def _set_box(self, box: Region) -> None:
        if self.mode == "image":
            self.result.image = box
        else:
            self.result.region = box
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
            self._set_box(box)
        self._draw()

    def _finish(self) -> None:
        r = self.result
        ready = {"location": r.point is not None,
                 "region": r.region is not None and r.region.w >= 3 and r.region.h >= 3,
                 "image": r.image is not None and r.image.w >= 3 and r.image.h >= 3}[self.kind]
        if ready:
            self._close("save", r)

    def _close(self, action: str, result: Result | None) -> None:
        self.window.destroy()
        self.done(action, result)

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
        hints = {"image": "click or drag  image   R  region   C  click point",
                 "location": "click  point", "region": "click or drag  region"}[self.kind]
        parts = [(f"{self.counter}  " if self.counter else "", Theme.MUTED, (Theme.FONT, 10)),
                 (self.title, Theme.TEXT, (Theme.BOLD, 11)),
                 (f"  {self.mode}  ", Theme.KIND_COLOR.get(self.kind, Theme.ACCENT), (Theme.FONT, 10)),
                 (f"{hints}    Enter  save   Space  new shot   Tab  skip   Backspace  undo   Esc  card",
                  Theme.MUTED, (Theme.FONT, 10))]
        if self.message:
            parts.append((f"    {self.message}", Theme.WARN, (Theme.FONT, 10)))
        x, y = 0, self.origin.h - 34
        ids = []
        for text, color, font in parts:
            if not text:
                continue
            item = c.create_text(x, y, anchor="w", text=text, fill=color, font=font, tags="bar")
            ids.append(item)
            x = c.bbox(item)[2]
        shift = (self.origin.w - x) / 2
        for item in ids:
            c.move(item, shift, 0)
        x0, y0, x1, y1 = c.bbox("bar")
        back = rounded(c, x0 - 18, y0 - 9, x1 + 18, y1 + 9, 16, fill=Theme.CARD, outline=Theme.LINE, tags="bar")
        c.tag_lower(back, ids[0])
