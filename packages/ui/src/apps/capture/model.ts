// The capture tool's state. See docs/tasks/T09-capture-overlay.md, "The model".

export type Kind = "image" | "region" | "point";
export const KINDS: Kind[] = ["image", "region", "point"];

export interface Box { x: number; y: number; w: number; h: number }
export interface Pt { x: number; y: number }

export interface SavedTarget {
  name: string;
  kind: Kind;
  image?: Box;
  region?: Box | { ref: string };
  offset?: { dx: number; dy: number };
  location?: Pt;
  thumb?: string;
}

export interface Draft {
  name: string;
  kind: Kind; // what's being made; the toolbar and Tab change it
  image?: Box;
  region?: Box | { ref: string }; // drawn, or another region target by name
  point?: { dx: number; dy: number } | Pt; // offset from the image's centre, or a fixed point
  existing?: SavedTarget; // when retaking
  say?: { slot: "bot" | "guide"; text: string; from?: string };
}

export function nextKind(kind: Kind): Kind {
  return KINDS[(KINDS.indexOf(kind) + 1) % KINDS.length];
}

/** Whether an image box is inside its region; shown as "inside ✓" or "outside ⚠" on the readout. */
export function inside(image: Box, region: Box): boolean {
  return image.x >= region.x && image.y >= region.y &&
    image.x + image.w <= region.x + region.w && image.y + image.h <= region.y + region.h;
}

/** A draft is ready to save when its kind has what it needs (at least 3 x 3 px for boxes). */
export function ready(draft: Draft): boolean {
  if (draft.kind === "point") return draft.point !== undefined;
  const box = draft.kind === "image" ? draft.image : draft.region;
  return !!box && "w" in box && box.w >= 3 && box.h >= 3;
}
