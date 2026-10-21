# T24 Text targets and masks

**Goal:** find and read text on screen, and ignore parts of an image that change.

**Depends on:** nothing. **Issues:** #55, #56. **Milestone:** v0.7.

## Outline

1. **Text targets:** `d.exists(Text("Play"))`, `d.read(region) -> str`, `d.read_number(region) -> float | None`. Windows' built-in OCR (`Windows.Media.Ocr` through `winrt`) first: no model download. Normalise case and spaces; digits-only mode for numbers.
2. **Masks:** a target's `.mask.png` (white = compare, black = ignore) used with `cv2.matchTemplate(..., mask=)` (`TM_CCORR_NORMED` supports masks). The capture tool (T09) gets a brush to paint the mask over a box.
3. The capture tool's readout shows the OCR'd text of a region, so a text target can be made from it in one click.

## Done when

A bot reads a reward amount; a character card with a changing level number matches with a mask.
