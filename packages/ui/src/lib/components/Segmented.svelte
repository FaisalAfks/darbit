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

<div class="segmented" data-variant={variant} role="radiogroup" aria-label={label}>
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
    display: inline-flex;
    gap: 2px;
    padding: 4px;
    border-radius: var(--radius-pill);
    background: var(--raised);
    max-width: 100%;
    overflow-x: auto;
    scrollbar-width: none;
  }
  [data-variant="nav"] {
    padding: 5px;
    background: var(--glass);
    backdrop-filter: blur(var(--blur));
    border: 1px solid var(--line);
    box-shadow: var(--shadow);
  }
  button {
    display: inline-flex;
    align-items: center;
    gap: var(--space-2);
    padding: 7px 14px;
    border: 0;
    border-radius: var(--radius-pill);
    background: none;
    color: var(--muted);
    font: 600 var(--size-s) / 1.2 var(--font-strong);
    white-space: nowrap;
    cursor: pointer;
    transition:
      background var(--fast) var(--ease),
      color var(--fast) var(--ease);
  }
  [data-variant="nav"] button {
    padding: 9px 18px;
    font-size: var(--size-m);
  }
  button:hover {
    color: var(--text);
  }
  [aria-checked="true"] {
    color: var(--text);
    background: var(--glass-strong);
    box-shadow: var(--shadow);
  }
  [data-variant="nav"] [aria-checked="true"] {
    color: var(--on-accent);
    background: var(--accent);
    box-shadow: none;
  }
</style>
