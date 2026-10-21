<!-- A floating pill of buttons. With avoidMouse it moves to the other edge when the mouse comes near. -->
<script lang="ts">
  import type { Snippet } from "svelte";

  let { edge = "bottom", avoidMouse = false, children }:
    { edge?: "top" | "bottom"; avoidMouse?: boolean; children: Snippet } = $props();
  let flipped = $state(false);
  // TODO(T03): with avoidMouse, set flipped when the mouse is within 80 px of the bar
  const at = $derived(flipped ? (edge === "top" ? "bottom" : "top") : edge);
</script>

<div class="bar appear" role="toolbar" data-edge={at}>{@render children()}</div>

<style>
  .bar {
    position: fixed; left: 50%; translate: -50% 0; display: flex; align-items: center; gap: var(--space-1);
    padding: var(--space-1) var(--space-2); max-width: 560px;
    background: var(--glass); backdrop-filter: blur(var(--blur)); border: 1px solid var(--line);
    border-radius: var(--radius-pill); box-shadow: var(--shadow);
  }
  [data-edge="bottom"] { bottom: var(--space-5); }
  [data-edge="top"] { top: var(--space-5); }
  .bar :global(hr) { width: 1px; height: 18px; border: 0; background: var(--line); margin: 0 var(--space-1); }
</style>
