<!-- A glass sheet that opens under the top pill: the bot switcher, the Studio's settings, Add step.
     Esc or a click outside closes it; its first control gets the focus when it opens.
     <Sheet title="Your bots" bind:open side="left">…</Sheet> -->
<script lang="ts">
  import type { Snippet } from "svelte";

  let {
    title,
    open = $bindable(false),
    side = "left",
    width = 560,
    actions,
    children,
  }: {
    title: string;
    open?: boolean;
    side?: "left" | "right";
    width?: number;
    actions?: Snippet;
    children: Snippet;
  } = $props();

  let sheet: HTMLElement | undefined = $state();

  $effect(() => {
    if (!open || !sheet) return;
    const first = sheet.querySelector<HTMLElement>("button, input, select, textarea, [tabindex]");
    first?.focus();

    function onkey(event: KeyboardEvent): void {
      if (event.key === "Escape") open = false;
    }
    function onpointer(event: PointerEvent): void {
      if (sheet && !sheet.contains(event.target as Node)) open = false;
    }
    window.addEventListener("keydown", onkey);
    // after the click that opened it has finished
    const wait = setTimeout(() => window.addEventListener("pointerdown", onpointer), 0);
    return () => {
      clearTimeout(wait);
      window.removeEventListener("keydown", onkey);
      window.removeEventListener("pointerdown", onpointer);
    };
  });
</script>

{#if open}
  <div bind:this={sheet} class="sheet appear" data-side={side} style:--width="{width}px" role="dialog" aria-label={title}>
    <header><h2>{title}</h2>{#if actions}{@render actions()}{/if}</header>
    {@render children()}
  </div>
{/if}

<style>
  .sheet {
    position: absolute;
    z-index: 20;
    top: calc(100% + var(--space-s));
    width: min(var(--width), calc(100vw - 2 * var(--space-l)));
    display: grid;
    gap: var(--space-l);
    padding: var(--space-xxl);
    border-radius: var(--radius-xl);
    background: var(--glass-strong);
    backdrop-filter: blur(var(--blur));
    border: 1px solid var(--line);
    box-shadow: var(--shadow);
  }
  [data-side="left"] {
    left: 0;
  }
  [data-side="right"] {
    right: 0;
  }
  header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: var(--space-m);
  }
  h2 {
    margin: 0;
    font: 650 var(--size-subtitle) / 1.2 var(--font-strong);
  }
</style>
