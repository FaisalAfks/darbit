# T06 Desktop windows

**Goal:** open any UI app as a desktop window: normal (the hub), full-screen overlay (capture, highlight), or a small always-on-top bar that never takes focus from the game (recorder, run panel, guide card).

**Depends on:** T01, T05. **Milestone:** v0.3.

## Files

- `src/darbit/desktop/__init__.py`: `open_window(app, kind, **options)`
- `src/darbit/desktop/windows.py`: the pywebview host and the Win32 style changes

## Steps

1. pywebview with the EdgeChromium (WebView2) backend. Each window loads `static/<app>/index.html?port=…&token=…` (or the Vite dev URL with `DARBIT_UI_DEV=1`).
2. Window kinds:
   - `normal`: frame, resizable, remembers its size and place (`settings` key `window.<app>`).
   - `overlay`: frameless, on top, covers one monitor exactly in **real pixels** (DPI-aware, as `platform/screen.py`), transparent background.
   - `bar`: frameless, on top, transparent, sized to its content, with `WS_EX_NOACTIVATE | WS_EX_TOOLWINDOW` set through `ctypes` after it's created, so clicking it doesn't take focus from the game and it isn't in Alt+Tab.
   - `clickthrough`: an overlay with `WS_EX_TRANSPARENT | WS_EX_LAYERED` so the mouse goes to the game (highlight).
3. pywebview wants the main thread. `open_window` runs the GUI loop on the main thread and the caller's work on a worker thread; a bot that opens a tool mid-run (`d.capture`) blocks until the window closes, as `input()` would.
4. One WebView2 environment shared by all windows (one browser process), so a second window opens in ~150 ms instead of ~600 ms. Measure both and put the numbers in the PR.
5. Closing: windows tell the server they're closing; the overlay frees its frame. No Tk anywhere.

## Contracts

- `open_window(app: str, kind: "normal" | "overlay" | "bar" | "clickthrough", monitor: int | None = None, query: dict | None = None) -> Window`
- `Window.close()`, `Window.wait()`.

## Done when

- The recorder bar sits on top of a game, can be clicked, and the game keeps keyboard focus (shown with a clip).
- The overlay covers a 150% scaled 2560×1600 screen with no gap and no blur (a 1-pixel checkerboard test image is sharp).

## Tests

- Offline: the window-style flags are computed by a pure function `styles(kind)`; test it.
- By hand: the clip and the checkerboard, in the PR.
