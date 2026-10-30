# T07 Freeze overlay test

**Goal:** prove the web overlay shows a frozen 2560×1600 screen sharply and smoothly before the capture tool moves to it.

**Depends on:** T06. **Issue:** #47. **Milestone:** v0.3.

## Steps

1. A throwaway `capture` app page that receives one frame (T05 binary frame), draws it on a full-size canvas (`createImageBitmap`, then `drawImage` once), and draws a dimmed copy with a bright cut-out box that follows the mouse, plus the Magnifier.
2. Measure and write down, on the owner's PC (2560×1600, 150%):
   - freeze to visible: from the hotkey to the first painted frame (target < 250 ms)
   - mouse move to repaint while dragging a box (target < 8 ms, 120 fps)
   - memory of the window process with one frame
   - WebP lossless vs PNG level 1: encode time, size, decode time
3. Check sharpness: a frame with a 1-pixel checkerboard must show no blur at 100% and 150% scaling (canvas size = real pixels, CSS size = real pixels / devicePixelRatio).
4. Decide: if all targets are met, T09 builds on the web overlay. If not, write down which one failed; the fallback is a native overlay (the current Tk one) styled with the same tokens, and T09 changes accordingly.

## Done when

The numbers and the decision are written in the issue and in `docs/ui/overlay-test.md`.

## Not in this task

Keeping the page: it's replaced by T09.
