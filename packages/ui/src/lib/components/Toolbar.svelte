<!-- A floating pill of buttons over the game: the capture toolbar, the recorder bar. Arrow keys move between
     its buttons. With avoidMouse it moves to the other edge when the mouse comes within 80 px of it.
     <Toolbar label="Capture tools" edge="bottom" avoidMouse>…</Toolbar> -->
<script lang="ts">
  import type { Snippet } from "svelte";

  const NEAR = 80; // px: how close the mouse comes before the bar moves out of the way

  let {
    label,
    edge = "bottom",
    avoidMouse = false,
    floating = true,
    children,
  }: { label: string; edge?: "top" | "bottom"; avoidMouse?: boolean; floating?: boolean; children: Snippet } = $props();

  let bar: HTMLElement | undefined = $state();
  let flipped = $state(false);
  const at = $derived(flipped ? (edge === "top" ? "bottom" : "top") : edge);

  $effect(() => {
    if (!avoidMouse || !floating) return;
    function onmove(event: PointerEvent): void {
      if (!bar) return;
      const box = bar.getBoundingClientRect();
      const dx = Math.max(box.left - event.clientX, 0, event.clientX - box.right);
      const dy = Math.max(box.top - event.clientY, 0, event.clientY - box.bottom);
      if (Math.hypot(dx, dy) < NEAR) flipped = !flipped;
    }
    window.addEventListener("pointermove", onmove);
    return () => window.removeEventListener("pointermove", onmove);
  });

  function onkeydown(event: KeyboardEvent): void {
    if (event.key !== "ArrowRight" && event.key !== "ArrowLeft") return;
    const controls = [...(bar?.querySelectorAll<HTMLElement>("button, select") ?? [])];
    const index = controls.indexOf(document.activeElement as HTMLElement);
    if (index < 0) return;
    const step = event.key === "ArrowRight" ? 1 : -1;
    controls[(index + step + controls.length) % controls.length].focus();
    event.preventDefault();
  }
</script>

<div bind:this={bar} class="bar appear" class:floating role="toolbar" aria-label={label} data-edge={at} tabindex="-1" {onkeydown}>
  {@render children()}
</div>

<style>
  .bar {
    display: flex;
    align-items: center;
    gap: var(--space-xs);
    padding: var(--space-s-nudge) var(--space-s) var(--space-s-nudge) var(--space-l);
    max-width: min(calc(20 * var(--space-xxxl)), calc(100vw - 2 * var(--space-l)));
    overflow-x: auto;
    scrollbar-width: none;
    background: var(--glass);
    backdrop-filter: blur(var(--blur));
    border: 1px solid var(--line);
    border-radius: var(--radius-pill);
    box-shadow: var(--shadow);
  }
  .floating {
    position: fixed;
    left: 50%;
    translate: -50% 0;
    z-index: 10;
  }
  .floating[data-edge="bottom"] {
    bottom: var(--space-xxl);
  }
  .floating[data-edge="top"] {
    top: var(--space-xxl);
  }
  .bar :global(hr) {
    width: 1px;
    height: var(--space-xl);
    flex: none;
    border: 0;
    background: var(--line);
    margin: 0 var(--space-xs);
  }
</style>
