<!-- The capture tool on a frozen screen. See docs/tasks/T09-capture-overlay.md and T10, T12. -->
<script lang="ts">
  import { register } from "$lib/actions";
  import IconButton from "$lib/components/IconButton.svelte";
  import Button from "$lib/components/Button.svelte";
  import Magnifier from "$lib/components/Magnifier.svelte";
  import TextSlot from "$lib/components/TextSlot.svelte";
  import Toolbar from "$lib/components/Toolbar.svelte";
  import { History } from "./history";
  import { type Draft, KINDS, nextKind } from "./model";

  let draft: Draft = $state({ name: "Untitled", kind: "image" });
  let frame: ImageBitmap | null = $state(null);
  let mouse = $state({ x: 0, y: 0 });
  let pinned = $state(false);
  let snapping = $state(true);
  const history = new History();

  // Every action is registered once; keys, buttons, the palette and menus all run these.
  register({ name: "capture.kind.cycle", label: "Next kind", run: () => (draft.kind = nextKind(draft.kind)) });
  register({ name: "capture.zoom.toggle", label: "Pin magnifier", run: () => (pinned = !pinned) });
  register({ name: "capture.snap.toggle", label: "Snapping", run: () => (snapping = !snapping) });
  // TODO(T09): capture.confirm, capture.cancel, capture.refreeze, capture.delete, nudges, smaller/bigger,
  // and the frame from onFrame(), the stage from createStage(), gestures from gesture()
  // TODO(T10): edit.undo / edit.redo through history, capture.confirm.next, rename, retake compare
</script>

<svelte:window onpointermove={(e) => { if (!pinned) mouse = { x: e.clientX, y: e.clientY }; }} />

<div class="stage"></div>

<div class="mag" style:left="{mouse.x + 28}px" style:top="{mouse.y + 28}px">
  <Magnifier {frame} x={mouse.x} y={mouse.y} />
</div>

<Toolbar label="Capture tools" edge="bottom" avoidMouse>
  <span class="name">{draft.name}</span>
  {#if draft.say}<TextSlot slot={draft.say.slot} text={draft.say.text} from={draft.say.from} />{/if}
  <hr />
  <div class="kinds" role="radiogroup" aria-label="Kind">
    {#each KINDS as kind}
      <button role="radio" aria-checked={draft.kind === kind} data-kind={kind} onclick={() => (draft.kind = kind)}>{kind}</button>
    {/each}
  </div>
  <hr />
  <IconButton action="capture.snap.toggle" label="Snapping" icon="⌗" pressed={snapping} />
  <IconButton action="capture.zoom.toggle" label="Pin magnifier" icon="⌕" pressed={pinned} />
  <IconButton action="edit.undo" label="Undo" icon="↶" />
  <IconButton action="capture.refreeze" label="New shot" icon="⟳" />
  <IconButton action="highlight.toggle" label="Highlight" icon="◎" />
  <hr />
  <Button action="capture.confirm" label="Save" variant="primary" />
</Toolbar>

<style>
  .stage { position: fixed; inset: 0; cursor: crosshair; }
  .mag { position: fixed; pointer-events: none; }
  .name { font: 600 var(--size-s) var(--font-strong); padding: 0 var(--space-2); white-space: nowrap; }
  .kinds { display: flex; background: var(--raised); border-radius: var(--radius-pill); padding: 2px; }
  .kinds button {
    border: 0; background: none; color: var(--muted); padding: 4px 10px; border-radius: var(--radius-pill);
    font: 600 var(--size-xs) var(--font-strong); cursor: pointer; text-transform: capitalize;
    transition: background var(--fast) var(--ease), color var(--fast) var(--ease);
  }
  .kinds button[aria-checked="true"] { color: var(--on-accent); background: var(--k); }
  [data-kind="image"] { --k: var(--kind-image); }
  [data-kind="region"] { --k: var(--kind-region); }
  [data-kind="point"] { --k: var(--kind-point); }
</style>
