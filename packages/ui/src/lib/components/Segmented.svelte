<!-- A pill of choices: the Studio's sections ("nav"), filters and tabs ("plain"), kinds in capture.
     Arrow keys move between them. <Segmented items={sections} bind:value variant="nav" label="Sections" /> -->
<script lang="ts">
  export interface Item {
    value: string;
    label: string;
    icon?: string;
  }

  let {
    items,
    value = $bindable(),
    label,
    variant = "plain",
  }: { items: Item[]; value: string; label: string; variant?: "nav" | "plain" } = $props();

  let buttons: HTMLButtonElement[] = $state([]);
  let marker = $state({ left: 0, width: 0, shown: false }); // the highlight that glides to the chosen item

  let bar: HTMLElement | undefined = $state();
  let size = $state(0); // bumps when the bar's size changes (fonts loading, the window resizing)

  $effect(() => {
    if (!bar) return;
    const watcher = new ResizeObserver(() => (size += 1));
    watcher.observe(bar);
    return () => watcher.disconnect();
  });

  $effect(() => {
    size; // measure again after a resize
    const index = items.findIndex((item) => item.value === value);
    const button = buttons[index];
    if (!button || !button.offsetWidth) {
      marker = { ...marker, shown: false };
      return;
    }
    marker = { left: button.offsetLeft, width: button.offsetWidth, shown: true };
  });

  function onkeydown(event: KeyboardEvent, index: number): void {
    let next = index;
    if (event.key === "ArrowRight") next = (index + 1) % items.length;
    else if (event.key === "ArrowLeft") next = (index - 1 + items.length) % items.length;
    else return;
    event.preventDefault();
    value = items[next].value;
    buttons[next]?.focus();
  }
</script>

<div class="segmented" bind:this={bar} data-variant={variant} role="radiogroup" aria-label={label}>
  <span class="marker" class:shown={marker.shown} style:translate="{marker.left}px 0" style:width="{marker.width}px" aria-hidden="true"></span>
  {#each items as item, index (item.value)}
    <button
      bind:this={buttons[index]}
      role="radio"
      aria-checked={item.value === value}
      tabindex={item.value === value ? 0 : -1}
      onclick={() => (value = item.value)}
      onkeydown={(event) => onkeydown(event, index)}
    >
      {#if item.icon}<span aria-hidden="true">{item.icon}</span>{/if}{item.label}
    </button>
  {/each}
</div>

<style>
  .segmented {
    position: relative;
    display: inline-flex;
    gap: 2px;
    padding: var(--space-xs);
    border-radius: var(--radius-pill);
    background: var(--raised);
    max-width: 100%;
    overflow-x: auto;
    scrollbar-width: none;
  }
  [data-variant="nav"] {
    padding: var(--space-xs);
    background: var(--glass);
    backdrop-filter: blur(var(--blur));
    border: 1px solid var(--line);
    box-shadow: var(--shadow);
  }
  button {
    display: inline-flex;
    align-items: center;
    gap: var(--space-s);
    min-height: var(--control-m);
    padding: 0 var(--space-m);
    border: 0;
    border-radius: var(--radius-pill);
    background: none;
    color: var(--muted);
    font: 600 var(--size-caption) / 1.2 var(--font-strong);
    white-space: nowrap;
    cursor: pointer;
    transition:
      background var(--duration-fast) var(--curve-easy-ease),
      color var(--duration-fast) var(--curve-easy-ease);
  }
  [data-variant="nav"] button {
    min-height: var(--control-l);
    padding: 0 var(--space-l);
    font-size: var(--size-body);
  }
  button:hover {
    color: var(--text);
  }
  .marker {
    position: absolute;
    top: var(--space-xs);
    bottom: var(--space-xs);
    left: 0;
    border-radius: var(--radius-pill);
    background: var(--glass-strong);
    box-shadow: var(--shadow);
    opacity: 0;
    transition:
      translate var(--duration-normal) var(--curve-decelerate),
      width var(--duration-normal) var(--curve-decelerate),
      opacity var(--duration-fast) var(--curve-easy-ease);
  }
  .marker.shown {
    opacity: 1;
  }
  [data-variant="nav"] .marker {
    background: var(--accent);
    box-shadow: 0 0 0 1px color-mix(in oklab, var(--accent) 40%, transparent);
  }
  button {
    position: relative;
  }
  [aria-checked="true"] {
    color: var(--text);
  }
  [data-variant="nav"] [aria-checked="true"] {
    color: var(--on-accent);
  }
  /* until the highlight is measured, the chosen item carries its own background */
  .segmented:not(:has(.marker.shown)) [aria-checked="true"] {
    background: var(--glass-strong);
  }
  [data-variant="nav"]:not(:has(.marker.shown)) [aria-checked="true"] {
    background: var(--accent);
  }
</style>
