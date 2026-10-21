"""A capture session: a card at the top centre of the screen walks through the targets.

The card slides out of the screen when the mouse has been away from it for a few
seconds, leaving its progress strip at the top edge, and slides back in when the
mouse comes near. F8 captures the current target; Ctrl+Alt+Q asks to finish.
"""
from __future__ import annotations

import ctypes
import time
import tkinter as tk
from collections.abc import Callable
from ctypes import wintypes
from pathlib import Path

import cv2
import numpy as np

from ..platform import screen
from .common import Item, Result, Theme, add_to_list, gradient, photo, rounded
from .overlay import Overlay
from .store import Saved, save_result, undo

HOTKEYS = {"f8": 0x77, "f9": 0x78, "f10": 0x79}
VK_CTRL, VK_ALT, VK_Q = 0x11, 0x12, 0x51

# the card's layout at 100% scaling; everything is multiplied by the display scaling
W, H = 820, 232
PEEK = 7  # what's left on screen when the card is away: its progress strip
THUMB_W, THUMB_H = 150, 100
HIDE_AFTER = 2.5  # seconds without the mouse near the card before it slides away
NEAR = 60  # how close the mouse must be


def _cursor() -> tuple[int, int]:
    point = wintypes.POINT()
    ctypes.windll.user32.GetCursorPos(ctypes.byref(point))
    return point.x, point.y


def _down(vk: int) -> bool:
    return bool(ctypes.windll.user32.GetAsyncKeyState(vk) & 0x8000)


class Session:
    def __init__(self, items: list[Item], folder: Path, hotkey: str = "f8", window: str | None = None,
                 list_file: Path | None = None) -> None:
        self.items, self.folder, self.window_name, self.list_file = items, folder, window, list_file
        self.index = 0
        self.saved: list[Saved] = []
        self.vk, self.hotkey = HOTKEYS[hotkey], hotkey.upper()
        self.state = "items" if items else "done"  # items, add, finish, done
        self.form: dict = {}
        self.adding_kind = "image"
        self.capturing = False
        self.toast: tuple[str, str] | None = None
        self._was_down = False
        self._quit_was_down = False
        self._near_at = time.monotonic()
        self._pinned_until = time.monotonic() + 3
        self._images: list[tk.PhotoImage] = []

        monitors = screen.monitors()
        desk = monitors[0] if monitors else screen.desktop()
        self.k = screen.scale_at(desk.x + desk.w // 2, desk.y + 10)
        self.w, self.h, self.peek = self.u(W), self.u(H), self.u(PEEK)
        self.x = desk.x + (desk.w - self.w) // 2
        self.shown_y = desk.y + self.u(14)
        self.hidden_y = desk.y - self.h + self.peek
        self.y = float(desk.y - self.h)

        self.root = tk.Tk()
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)
        self.root.attributes("-transparentcolor", Theme.KEY)
        self.root.configure(bg=Theme.KEY)
        self.root.geometry(f"{self.w}x{self.h}+{self.x}+{round(self.y)}")
        self.canvas = tk.Canvas(self.root, width=self.w, height=self.h, bg=Theme.KEY, highlightthickness=0)
        self.canvas.pack()
        self._render()
        self._tick()

    # ----------------------------------------------------------------- units

    def u(self, value: float) -> int:
        """A layout size at 100% scaling, in real pixels."""
        return round(value * self.k)

    def font(self, size: float, bold: bool = False) -> tuple[str, int]:
        return (Theme.BOLD if bold else Theme.FONT, -self.u(size))  # negative: pixels, not points

    # --------------------------------------------------------------- drawing

    def _render(self) -> None:
        c = self.canvas
        c.delete("all")
        for child in self.root.winfo_children():
            if isinstance(child, tk.Entry):
                child.destroy()
        self._images.clear()
        rounded(c, 0, 0, self.w - 1, self.h - 1, self.u(20), fill=Theme.CARD, outline=Theme.LINE)
        {"items": self._render_item, "add": self._render_add, "finish": self._render_finish,
         "done": self._render_done}[self.state]()
        self._render_progress()

    def _render_progress(self) -> None:
        c, u = self.canvas, self.u
        y0, y1 = self.h - self.peek + 1, self.h - u(2)
        c.create_rectangle(u(20), y0, self.w - u(20), y1, fill=Theme.LINE, width=0)
        done = min(self.index, len(self.items)) / max(1, len(self.items))
        right = u(20) + round((self.w - u(40)) * done)
        if right > u(20):
            gradient(c, u(20), y0, right, y1, Theme.ACCENT, Theme.ACCENT2)

    def _header(self, text: str, color: str) -> None:
        c, u = self.canvas, self.u
        c.create_text(u(28), u(28), anchor="w", text=text, fill=color, font=self.font(13, True))
        if self.toast and self.toast[0]:
            c.create_text(self.w - u(28), u(28), anchor="e", text=self.toast[0], fill=self.toast[1],
                          font=self.font(13))

    def _button(self, right: float, text: str, action: Callable[[], None], style: str = "plain") -> float:
        """A pill button ending at `right`; returns its left edge."""
        c, u = self.canvas, self.u
        fill, hover, color = {"primary": (Theme.ACCENT, "#8fdcfc", "#0b1220"),
                              "danger": (Theme.RAISED, "#3a2326", Theme.DANGER),
                              "plain": (Theme.RAISED, "#30333c", Theme.TEXT)}[style]
        tag = f"button-{text}"
        y = self.h - u(36)
        label = c.create_text(0, y, anchor="center", text=text, fill=color, font=self.font(14, True), tags=tag)
        x0, _, x1, _ = c.bbox(label)
        width = x1 - x0 + u(36)
        c.coords(label, right - width / 2, y)
        back = rounded(c, right - width, y - u(17), right, y + u(17), u(17), fill=fill, outline="", tags=tag)
        c.tag_lower(back, label)
        c.tag_bind(tag, "<Enter>", lambda _e: (c.itemconfigure(back, fill=hover), c.configure(cursor="hand2")))
        c.tag_bind(tag, "<Leave>", lambda _e: (c.itemconfigure(back, fill=fill), c.configure(cursor="")))
        c.tag_bind(tag, "<ButtonRelease-1>", lambda _e: action())
        return right - width

    def _thumbnail(self, x0: int, image: np.ndarray | None, caption: str, empty: str, risky: bool | None) -> None:
        c, u = self.canvas, self.u
        y0, w, h = u(44), u(THUMB_W), u(THUMB_H)
        rounded(c, x0, y0, x0 + w, y0 + h, u(12), fill=Theme.RAISED, outline=Theme.LINE)
        c.create_text(x0 + w / 2, y0 + h + u(13), text=caption, fill=Theme.MUTED, font=self.font(10, True))
        if image is None:
            c.create_text(x0 + w / 2, y0 + h / 2, text=empty, fill=Theme.MUTED, font=self.font(12))
            return
        ih, iw = image.shape[:2]
        scale = min((w - u(12)) / iw, (h - u(12)) / ih, 4 * self.k)
        small = cv2.resize(image, (max(1, round(iw * scale)), max(1, round(ih * scale))),
                           interpolation=cv2.INTER_AREA if scale < 1 else cv2.INTER_NEAREST)
        thumb = photo(small)
        self._images.append(thumb)
        c.create_image(x0 + w / 2, y0 + h / 2, image=thumb)
        if risky is not None:
            tone = Theme.WARN if risky else Theme.OK
            r = u(11)
            cx, cy = x0 + w - u(2), y0 + u(2)
            c.create_oval(cx - r, cy - r, cx + r, cy + r, fill=tone, outline=Theme.CARD, width=u(2))
            c.create_text(cx, cy, text="!" if risky else "✓", fill="#0b1220", font=self.font(12, True))

    def _render_item(self) -> None:
        c, u = self.canvas, self.u
        item = self.items[self.index]
        color = Theme.KIND_COLOR[item.kind]
        self._header(f"CAPTURE  ·  {self.index + 1} OF {len(self.items)}  ·  {item.kind.upper()}", Theme.MUTED)

        # the last capture on the right
        last = self.saved[-1] if self.saved else None
        thumb_x = self.w - u(28) - u(THUMB_W)
        self._thumbnail(thumb_x, last.thumb if last else None, "LAST SAVED", "none yet",
                        None if last is None or last.thumb is None else last.risky)

        # kind badge, name, what it is, and what to do
        cx, cy, r = u(52), u(78), u(24)
        c.create_oval(cx - r, cy - r, cx + r, cy + r, fill=Theme.RAISED, outline=color, width=u(2))
        c.create_text(cx, cy, text=Theme.KIND_GLYPH[item.kind], fill=color, font=self.font(21))
        text_x, text_right = u(92), thumb_x - u(24)
        self._fit(c.create_text(text_x, u(66), anchor="w", text=item.name, fill=Theme.TEXT,
                                font=self.font(28, True)), item.name, text_right)
        if item.note:
            self._fit(c.create_text(text_x, u(100), anchor="w", text=item.note, fill=Theme.TEXT,
                                    font=self.font(15)), item.note, text_right)
        what = {"image": "box the image", "location": "click the point", "region": "box the region"}[item.kind]
        hint_y = u(132) if item.note else u(102)
        t = c.create_text(text_x, hint_y, anchor="w", text="Press", fill=Theme.MUTED, font=self.font(14))
        x = c.bbox(t)[2] + u(9)
        key = c.create_text(x + u(9), hint_y, anchor="w", text=self.hotkey, fill=Theme.TEXT,
                            font=self.font(13, True))
        kx0, ky0, kx1, ky1 = c.bbox(key)
        cap = rounded(c, kx0 - u(8), ky0 - u(3), kx1 + u(8), ky1 + u(3), u(7), fill=Theme.RAISED,
                      outline=Theme.LINE)
        c.tag_lower(cap, key)
        c.create_text(kx1 + u(16), hint_y, anchor="w", text=f"when it's on screen, {what}, Enter",
                      fill=Theme.MUTED, font=self.font(14))

        right = self.w - u(28)
        right = self._button(right, "Done", self._ask_finish, "primary") - u(10)
        right = self._button(right, "Skip", self._skip) - u(10)
        if self.index > 0:
            right = self._button(right, "Back", self._back) - u(10)
        if self.saved:
            right = self._button(right, "Undo", self._undo) - u(10)
        self._button(right, "+ Add", self._open_add)
        c.create_text(u(28), self.h - u(36), anchor="w", text="Ctrl+Alt+Q  finish", fill=Theme.MUTED,
                      font=self.font(12))

    def _fit(self, label: int, text: str, right: float) -> None:
        """Shorten a text with an ellipsis until it ends before `right`."""
        c = self.canvas
        while c.bbox(label)[2] > right and len(text) > 4:
            text = text[:-2]
            c.itemconfigure(label, text=text + "…")

    # ----------------------------------------------------------- add a target

    def _entry(self, x: float, y: float, width: float, value: str = "") -> tk.Entry:
        entry = tk.Entry(self.root, bg=Theme.RAISED, fg=Theme.TEXT, insertbackground=Theme.TEXT, relief="flat",
                         font=self.font(15), highlightthickness=self.u(1), highlightbackground=Theme.LINE,
                         highlightcolor=Theme.ACCENT)
        entry.insert(0, value)
        self.canvas.create_window(x, y, anchor="w", window=entry, width=width, height=self.u(36))
        return entry

    def _render_add(self) -> None:
        c, u = self.canvas, self.u
        self._header("ADD A TARGET" + (f"  ·  ALSO SAVED TO {self.list_file.name}" if self.list_file else ""),
                     Theme.MUTED)
        c.create_text(u(28), u(72), anchor="w", text="Name", fill=Theme.MUTED, font=self.font(13))
        c.create_text(u(28), u(120), anchor="w", text="What", fill=Theme.MUTED, font=self.font(13))
        name = self._entry(u(92), u(72), u(330), self.form.get("name", ""))
        note = self._entry(u(92), u(120), self.w - u(92) - u(28), self.form.get("note", ""))
        self.form = {"name_entry": name, "note_entry": note}
        x = u(440)
        for kind in ("image", "location", "region"):
            chosen = kind == self.adding_kind
            tag = f"kind-{kind}"
            label = c.create_text(0, u(72), anchor="w", text=f"{Theme.KIND_GLYPH[kind]}  {kind}",
                                  fill="#0b1220" if chosen else Theme.TEXT, font=self.font(13, True), tags=tag)
            x0, _, x1, _ = c.bbox(label)
            width = x1 - x0 + u(28)
            c.coords(label, x + u(14), u(72))
            back = rounded(c, x, u(72) - u(17), x + width, u(72) + u(17), u(17),
                           fill=Theme.KIND_COLOR[kind] if chosen else Theme.RAISED, outline="", tags=tag)
            c.tag_lower(back, label)
            c.tag_bind(tag, "<ButtonRelease-1>", lambda _e, k=kind: self._pick_kind(k))
            c.tag_bind(tag, "<Enter>", lambda _e: c.configure(cursor="hand2"))
            c.tag_bind(tag, "<Leave>", lambda _e: c.configure(cursor=""))
            x += width + u(8)
        right = self._button(self.w - u(28), "Add", self._add, "primary") - u(10)
        self._button(right, "Cancel", self._cancel_add)
        c.create_text(u(28), self.h - u(36), anchor="w", text="Goes next in the session", fill=Theme.MUTED,
                      font=self.font(12))
        for entry in (name, note):
            entry.bind("<Return>", lambda _e: self._add())
            entry.bind("<Escape>", lambda _e: self._cancel_add())
        self.root.after(30, lambda: name.winfo_exists() and (self.root.focus_force(), name.focus_set()))

    def _keep_form(self) -> None:
        if "name_entry" in self.form:
            self.form = {"name": self.form["name_entry"].get(), "note": self.form["note_entry"].get()}

    def _pick_kind(self, kind: str) -> None:
        self._keep_form()
        self.adding_kind = kind
        self._render()

    def _open_add(self) -> None:
        self.form = {}
        self.state = "add"
        self._show(pin=3600)

    def _cancel_add(self) -> None:
        self.form = {}
        self.state = "items" if self.index < len(self.items) else "done"
        self._show()

    def _add(self) -> None:
        self._keep_form()
        name = self.form.get("name", "").strip().removesuffix(".png")
        if not name:
            return
        item = Item(name, self.adding_kind, self.form.get("note", "").strip())
        self.items.insert(self.index, item)
        if self.list_file is not None:
            add_to_list(self.list_file, item)
        self.form = {}
        self.state = "items"
        self._show((f"added {name}", Theme.ACCENT))

    def _render_finish(self) -> None:
        c, u = self.canvas, self.u
        count = len(self.saved)
        self._header("FINISH", Theme.MUTED)
        c.create_text(u(28), u(66), anchor="w", text=f"{count} new capture{'s' if count != 1 else ''} this session",
                      fill=Theme.TEXT, font=self.font(28, True))
        c.create_text(u(28), u(102), anchor="w", text="Keep them, or delete them and put back what they replaced.",
                      fill=Theme.MUTED, font=self.font(15))
        right = self._button(self.w - u(28), "Keep", lambda: self._close(keep=True), "primary") - u(10)
        right = self._button(right, "Delete all", lambda: self._close(keep=False), "danger") - u(10)
        self._button(right, "Cancel", self._cancel_finish)

    def _render_done(self) -> None:
        c, u = self.canvas, self.u
        self._header("ALL DONE", Theme.OK)
        c.create_text(u(28), u(66), anchor="w", text="Everything is captured", fill=Theme.TEXT,
                      font=self.font(28, True))
        c.create_text(u(28), u(102), anchor="w", text=f"{len(self.saved)} saved in {self.folder}", fill=Theme.MUTED,
                      font=self.font(15))
        right = self._button(self.w - u(28), "Finish", self._ask_finish, "primary") - u(10)
        if self.saved:
            right = self._button(right, "Undo", self._undo) - u(10)
        self._button(right, "+ Add", self._open_add)

    # --------------------------------------------------------------- actions

    def _show(self, toast: tuple[str, str] | None = None, pin: float = 2.5) -> None:
        if toast is not None:
            self.toast = toast
        if self.state == "items" and self.index >= len(self.items):
            self.state = "done"
        self._pinned_until = time.monotonic() + pin
        self._render()

    def _skip(self) -> None:
        if self.index < len(self.items):
            self.index += 1
            self._show(("skipped", Theme.MUTED))

    def _back(self) -> None:
        if self.index > 0:
            self.index -= 1
            self.state = "items"
            self._show(("", Theme.MUTED))

    def _undo(self) -> None:
        if not self.saved:
            return
        last = self.saved.pop()
        undo(last)
        print(f"undone {last.item.name}", flush=True)
        if last.item in self.items:
            self.index = self.items.index(last.item)
        self.state = "items"
        self._show((f"undone {last.item.name}", Theme.WARN))

    def _ask_finish(self) -> None:
        if not self.saved:
            self.root.destroy()
            return
        self.state = "finish"
        self._show(pin=3600)

    def _cancel_finish(self) -> None:
        self.state = "items"
        self._show()

    def _close(self, keep: bool) -> None:
        if keep:
            print(f"kept {len(self.saved)} captures", flush=True)
        else:
            for saved in reversed(self.saved):
                undo(saved)
            print(f"deleted {len(self.saved)} captures from this session", flush=True)
        self.root.destroy()

    # --------------------------------------------------------------- capture

    def _capture(self) -> None:
        self.capturing = True
        self.root.withdraw()
        self.root.update()
        time.sleep(0.15)  # let the card disappear before the shot
        shot, origin = screen.grab()
        item = self.items[self.index]

        def done(result: Result | None) -> None:
            self.capturing = False
            self.root.deiconify()
            self.root.attributes("-topmost", True)
            if result is None:
                self._show(("cancelled", Theme.MUTED))
                return
            saved = save_result(self.folder, item, result, shot, origin, self._window_size())
            print(saved.message, flush=True)
            self.saved.append(saved)
            self.index += 1
            tone = Theme.WARN if saved.risky else Theme.OK
            text = f"saved {item.name}" + (f"  ·  risky {saved.elsewhere:.2f}" if saved.risky else "")
            self._show((text, tone))

        Overlay(self.root, shot, origin, item.kind, item.name, done)

    def _window_size(self) -> list[int] | None:
        if not self.window_name:
            return None
        from ..runtime import apps
        area = apps.window(self.window_name)
        return [area.w, area.h] if area else None

    # ------------------------------------------------------------------ loop

    def _tick(self) -> None:
        now = time.monotonic()
        down = _down(self.vk)
        if down and not self._was_down and not self.capturing and self.state == "items":
            self._capture()
        self._was_down = down
        quit_down = _down(VK_CTRL) and _down(VK_ALT) and _down(VK_Q)
        if quit_down and not self._quit_was_down and not self.capturing:
            self._ask_finish()
        self._quit_was_down = quit_down

        mx, my = _cursor()
        near = self.x - NEAR <= mx <= self.x + self.w + NEAR and my <= round(self.y) + self.h + NEAR
        if near:
            self._near_at = now
        keep = near or now < self._pinned_until or now - self._near_at < HIDE_AFTER or self.state in ("finish", "add")
        target = self.shown_y if keep else self.hidden_y
        if abs(target - self.y) > 0.5:
            self.y += (target - self.y) * 0.22
            self.root.geometry(f"+{self.x}+{round(self.y)}")
        self.root.after(15, self._tick)

    def run(self) -> None:
        try:
            self.root.mainloop()
        except KeyboardInterrupt:
            print(f"stopped; {len(self.saved)} captures kept", flush=True)
