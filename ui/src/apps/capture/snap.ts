// Snapping in the window, the same rules as src/darbit/capture/engine/snap.py; both pass
// tests/data/capture/snap_cases.json. See docs/tasks/T08-capture-engine.md step 4.
import type { Box } from "./model";

export interface Lines { h: [number, number, number][]; v: [number, number, number][] }
export type Edge = "left" | "top" | "right" | "bottom";
export type Guide = [number, number, number, number];

export function snapBox(
  lines: Lines, box: Box, moving: Set<Edge>, reach = 6, border: "include" | "exclude" = "include",
): { box: Box; guides: Guide[] } {
  // TODO(T09): each moving edge to the nearest line within reach that overlaps that side by >= 30%
  return { box, guides: [] };
}
