// Undo and redo of the draft. A burst of the same nudge key is one step. See docs/tasks/T10-capture-editing.md.
import type { Draft } from "./model";

export class History {
  private past: Draft[] = [];
  private future: Draft[] = [];
  private burst: string | null = null;

  /** Remember the draft before a change. `burst` groups repeated changes (e.g. "nudge:right") into one step. */
  push(before: Draft, burst: string | null = null): void {
    if (burst !== null && burst === this.burst) return;
    this.burst = burst;
    this.past.push(structuredClone(before));
    this.future = [];
  }

  undo(now: Draft): Draft | null {
    const before = this.past.pop();
    if (!before) return null;
    this.future.push(structuredClone(now));
    this.burst = null;
    return before;
  }

  redo(now: Draft): Draft | null {
    const after = this.future.pop();
    if (!after) return null;
    this.past.push(structuredClone(now));
    this.burst = null;
    return after;
  }

  get size(): number {
    return this.past.length;
  }
}
