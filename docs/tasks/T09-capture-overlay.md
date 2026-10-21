# T09 Capture overlay

**Goal:** the frozen-screen capture tool on the web UI: select, draw and link images, regions and points with the mouse or the keyboard, see exactly where and how big everything is, and save.

**Depends on:** T03, T04, T07, T08. **Issue:** #48. **Milestone:** v0.3. **Keys:** the `[capture]` and `[mouse]` scopes of `keymap.toml`.

## Files

- `ui/src/apps/capture/App.svelte`: the window: frame layer, shapes layer, chips, toolbar, magnifier
- `ui/src/apps/capture/stage.ts`: the Konva stage (frame, dim, bright cut-outs, shapes, handles)
- `ui/src/apps/capture/gestures.ts`: mouse and keys → actions
- `ui/src/apps/capture/snap.ts`: the port of `snap_box` (T08)
- `ui/src/apps/capture/model.ts`: the capture state (below)
- `src/darbit/capture/service.py`: server handlers `capture.freeze`, `capture.candidates`, `capture.save`, `capture.targets`
- `src/darbit/core/targets.py`: named regions (step 8)

## The model

```ts
type Kind = "image" | "region" | "point";
interface Draft {
  name: string;               // "Bag.Character"
  kind: Kind;                 // what's being made; the toolbar and Tab change it
  image?: Box;                // the picture, for kind image
  region?: Box | { ref: string };   // its search region: drawn, or another region target by name
  point?: { dx: number; dy: number } | Pt;  // click offset from the image centre, or a fixed point
  existing?: SavedTarget;     // when retaking: what's saved now
}
```

## Steps

1. **Freeze:** `capture.freeze` grabs every monitor, starts `prepare()` (T08), and sends the frame (binary) and then the `Lines`. One overlay window per monitor (T06 `overlay`).
2. **Layers:** the frame dimmed to 42%; each box shows the frame at full brightness inside it; shapes on top; DOM chips and the toolbar above. Kind colours: image `--kind-image` solid, region `--kind-region` dashed, point `--kind-point` crosshair.
3. **Kinds without memorised letters:**
   - the toolbar's segmented control `Image | Region | Point`, and `Tab` cycles it;
   - gestures always work whatever the kind: drag draws the current kind, `Shift`+drag draws a region, `Ctrl`+click sets the click point, click selects (T08 `candidates`, again for bigger).
4. **Readouts for every kind** (the old tool only showed an image's size): image `w × h`, region `x, y · w × h`, point `x, y` and, on an image, `+dx, +dy` from its centre. Click a readout to type exact numbers (T03 Readout).
5. **The click point** starts at the image's centre and shows as a small handle; drag it, `Ctrl`+click elsewhere, or reset it from its chip. It's saved as the target's `offset`.
6. **Magnifier:** follows the mouse; wheel 4×–16×; `z` pins it. It draws the boxes, handles, point and snap guides too (the old one only showed the screen, so a box under it was hidden). While a handle is dragged it centres on that corner.
7. **Handles:** eight on the selected box (Konva Transformer, no rotation); drag inside to move. Snapping (T08) on the moving edges, guides drawn while snapping, `Alt` held turns it off.
8. **Linking a region:** the region chip of an image offers `Link ▾` with the project's region targets (from `capture.targets`) and `Draw`. A linked region is drawn with its name, and the image readout shows `inside ✓` or `outside ⚠`. When an image is drawn inside an existing region target, the chip suggests it ("In Measure.bagMenuRegion? Link"). Saved as `"region": "Measure.bagMenuRegion"` in the image's `.json`: change `core/targets.load` to accept a region **name** and resolve it from the same images folder, with a test, and keep reading `[x, y, w, h]`.
9. **Retake:** when the target exists, its saved box, region and point are loaded, and its saved image is shown as a faint ghost at its place. Hold `C` to see the saved image over the new box.
10. **Text:** the toolbar's left end shows the target's name and a `TextSlot` (guide or bot text, T12) in one line; the `tool` slot shows the one hint that matters right now ("click again for bigger").
11. **Save:** `Enter` or the Save button sends `capture.save` with the draft; the server writes `.png` and `.json` with `store.save_result` (same files as today: real pixels, `scale`, `window`) and returns undo data for T10. A toast confirms.
12. **Toolbar** (one pill, bottom centre, moves up when the mouse nears it): name and text · kind control · `Smaller`/`Bigger` · snap toggle · zoom pin · undo/redo · new shot · highlight · Save · Close. Every button shows its key on hover.

## Contracts

- Messages `capture.freeze {monitors?}`, `capture.candidates {x, y, kind} -> [Box]` (when the window wants them from the server), `capture.save {draft} -> {saved, undo}`, `capture.targets {} -> [SavedTarget]`.
- Image `.json` `region` may be a name (string) or `[x, y, w, h]`.

## Done when

- The owner captures an image, its linked region and its click point with the mouse only, and again with the keyboard only, on a 150% screen, and the saved files work in a bot.
- Readouts show for all three kinds; the magnifier shows the box under it.

## Tests

- `snap.ts` passes `snap_cases.json`; `gestures.ts` mapping tests (event → action) with vitest.
- Python: `capture.save` writes the expected files from a draft; `targets.load` resolves a region name.

## Not in this task

Undo history beyond one step, adding new names, renaming (T10); the guide (T12).
