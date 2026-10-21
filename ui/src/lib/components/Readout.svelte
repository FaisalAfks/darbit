<!-- Where and how big, for every kind: image "w × h", region "x, y · w × h", point "x, y".
     Click to type exact numbers. -->
<script lang="ts">
  type Value = { x: number; y: number; w?: number; h?: number };
  let { x, y, w, h, kind, onchange }:
    Value & { kind: "image" | "region" | "point"; onchange?: (v: Value) => void } = $props();
  let editing = $state(false);
  // TODO(T03): when editing, four number fields; Enter calls onchange, Esc cancels
</script>

<button class="readout num" data-kind={kind} onclick={() => (editing = true)}>
  {#if kind === "image" && w !== undefined}{w} × {h}{:else}{x}, {y}{#if w !== undefined} · {w} × {h}{/if}{/if}
</button>

<style>
  .readout {
    padding: 1px 7px; border: 0; border-radius: var(--radius-s); cursor: text;
    font-size: var(--size-xs); color: var(--on-accent); background: var(--k, var(--accent));
  }
  [data-kind="image"] { --k: var(--kind-image); }
  [data-kind="region"] { --k: var(--kind-region); }
  [data-kind="point"] { --k: var(--kind-point); }
</style>
