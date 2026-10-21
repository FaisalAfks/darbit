# T08 Capture engine: click to select and snapping

**Goal:** the pure image work behind the capture tool, rebuilt so click-to-select works for regions of any size and snapping lands where it should. No UI in this task.

**Depends on:** nothing. **Issue:** #38. **Milestone:** v0.3.

## What's wrong today (in `capture/overlay.py`)

- **Click to select has size limits.** A fill bigger than 20% of the screen falls back to `_shape_at`, which only looks in a 900×600 window around the click and drops shapes over 70% of it; `_grow` stops at 6% of the screen. So a whole menu or window can't be selected, which is what regions usually are.
- **Snapping pulls points, not edges.** `snap()` moves each corner to the strongest edge column and row within 6 px, counted over a short span. On textured game UIs that's often a texture line; it also snaps both corners independently, so a box jumps while it's dragged. Canny puts edge pixels on one side of a border, so boxes are often one pixel inside or outside it, inconsistently. There's no sign on screen of what it snapped to.

## Files

- `src/darbit/capture/engine/__init__.py`: `prepare()`, `Prepared`
- `src/darbit/capture/engine/select.py`: `candidates()`
- `src/darbit/capture/engine/snap.py`: `lines()`, `snap_box()`
- `tests/test_capture_engine.py`, `tests/data/capture/`: saved screenshots with expected boxes (the owner's game screens cut down, plus synthetic ones)
- `tests/data/capture/snap_cases.json`: shared cases that the TypeScript port (T09) runs too

## Steps

1. **`prepare(shot) -> Prepared`**, once per freeze, on a worker thread while the overlay appears. Holds the grey image, Canny edges, a half-size edge map, and the straight lines (step 3). Budget: ≤ 120 ms for 2560×1600 (done: about 60–75 ms).
2. **`candidates(prep, x, y, kind) -> list[Region]`**: every sensible box around the point, **smallest first**. A click selects `pick(boxes)`: the first at least 40×30, so a click on a button's letter starts on the button. Clicking again on the same spot (within 4 px) steps to the next bigger one; right-click → "Smaller" steps back. One gesture, any size:
   - `image`: today's colour fill and grow (`_fill`, `_grow`) give the small ones (a letter, an icon, a button), without the screen-share caps.
   - `region`: rectangles from the half-size edge map, over the **whole** screen: contours whose fill of their bounding box is ≥ 85% or that simplify to four corners (`approxPolyDP`), at least 80×60 real pixels, up to the full monitor. Panels, windows and lists come out as nested rectangles.
   - Remove near-duplicates (IoU > 0.9) and always end with the whole monitor.
3. **`lines(gray) -> Lines`**: straight runs (≥ 16 px) of **boundaries between two pixels** where the brightness jumps by 24 or more, not Canny's edge pixels: Canny puts its pixel on either side of a border depending on the texture next to it, which made boxes land one pixel off. A line at x = 300 is between pixels 299 and 300, so a drawn border has two exact lines, its outer and inner side. `{"h": [[y, x0, x1], ...], "v": [[x, y0, y1], ...]}`, the longest 4000. They're sent to the overlay once per freeze, so snapping runs in the window without a round trip.
4. **`snap_box(lines, box, moving, reach=6, border="include") -> (Region, guides)`**: only the edges being moved (`moving` ⊆ `{"left","top","right","bottom"}`) snap, each to the nearest line within `reach` that **runs along at least 30% of that side**. Lines within 8 px of it on the same side are the same border: `"include"` walks outward to the border's outer side (the border is in the image), `"exclude"` inward to its inner side. Returns the guides it snapped to, so the overlay can draw them.
5. A drag snaps only the corner being dragged; the fixed corner was snapped at press. Alt held: no snapping.
6. Port `snap_box` to `ui/src/apps/capture/snap.ts` (T09) and keep both passing `snap_cases.json`.

## Contracts

- `Prepared`, `candidates`, `lines`, `snap_box` signatures as in the placeholders.
- The `Lines` JSON shape above (T09 reads it).

## Done when

- On the saved game screens: one click selects the button; repeated clicks reach the whole menu window and then the screen. Region clicks on the Bag, Speed Raid and Play menus give the window rectangle on the first or second click.
- Snapping cases: a box dragged near a 1 px border lands on it on all four sides, the same way every time; a box over a textured background doesn't move.

## Tests

- `candidates` against the expected boxes in `tests/data/capture/*.json` (within 2 px).
- `snap_cases.json`: input box, moving edges, expected box.
- Timing test marked `slow`: `prepare` on a 2560×1600 image under 200 ms on CI.

## Not in this task

Drawing anything; the old Tk overlay keeps its own code until T13.
