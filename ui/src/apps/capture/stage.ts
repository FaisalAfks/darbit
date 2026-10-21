// The Konva stage: the frozen frame dimmed, bright cut-outs inside boxes, shapes, handles and snap guides.
// See docs/tasks/T09-capture-overlay.md step 2.
import type { Draft } from "./model";
import type { Guide } from "./snap";

export interface Stage {
  setFrame(frame: ImageBitmap): void;
  draw(draft: Draft, guides: Guide[]): void;
  destroy(): void;
}

export function createStage(container: HTMLDivElement, width: number, height: number): Stage {
  // TODO(T09): Konva.Stage with three layers (frame, shapes, handles); a Transformer without rotation on
  // the selected box; the bright cut-out redrawn at most once per animation frame
  throw new Error("TODO(T09)");
}
