# T22 Window-relative targets

**Goal:** targets keep working when the game window moves, changes size, or runs on a screen with another scaling.

**Depends on:** nothing. **Issue:** #13. **Milestone:** v0.2.

## Files

- `src/darbit/core/targets.py`: `scale`, `window` already saved; add `origin` (the window's top-left when captured)
- `src/darbit/runtime/find.py`: place regions and locations relative to the window, rescale images
- `src/darbit/platform/windows.py`: the window's client rectangle in real pixels
- `src/darbit/settings.py`: `settings.window = "Roblox"` (or from `darbit.toml`, T17)

## Steps

1. When `settings.window` is set, every region and location is stored relative to that window's client area at capture time (the capture tool saves `origin` and `window`).
2. At run time: offset by the window's current place; scale by `current_size / captured_size` (width ratio; warn if the aspect ratio changed).
3. Images: when the ratio isn't 1, resize the template once (`cv2.INTER_AREA` down, `INTER_LINEAR` up) and cache it by ratio. If the best score is low, try ratios ±5% and ±10% once and remember the one that worked.
4. Without `settings.window`, everything stays as it is.
5. `darbit check` lists targets captured at another scale or window size.

## Done when

ad-bot finds its targets with the Roblox window moved and at 1600×1000 instead of full screen.

## Tests

Offsets and scaling on saved screens resized by known ratios.
