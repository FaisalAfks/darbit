<!-- A round icon button for pills and toolbars: its label and keys show in the tooltip.
     <IconButton action="run.pause" label="Pause" icon="❚❚" />   <IconButton label="Snapping" icon="⌗" bind:pressed /> -->
<script lang="ts">
  import { run } from "$lib/actions";
  import { keysFor } from "$lib/keymap";
  import { tip } from "$lib/tooltip";

  let {
    label,
    icon,
    action,
    onclick,
    pressed = $bindable(),
    disabled = false,
  }: {
    label: string;
    icon: string;
    action?: string;
    onclick?: () => void;
    pressed?: boolean; // a toggle when given
    disabled?: boolean;
  } = $props();

  const keys = $derived(action ? keysFor(action) : undefined);

  function press(): void {
    if (pressed !== undefined) pressed = !pressed;
    if (onclick) onclick();
    else if (action) run(action);
  }
</script>

<button
  class="icon-button"
  {disabled}
  onclick={press}
  aria-label={label}
  aria-pressed={pressed}
  aria-keyshortcuts={keys}
  use:tip={{ label, keys }}
>
  <span aria-hidden="true">{icon}</span>
</button>

<style>
  .icon-button {
    width: 36px;
    height: 36px;
    flex: none;
    display: inline-grid;
    place-items: center;
    border: 0;
    border-radius: var(--radius-pill);
    background: transparent;
    color: var(--muted);
    font-size: var(--size-m);
    cursor: pointer;
    transition:
      background var(--fast) var(--ease),
      color var(--fast) var(--ease);
  }
  .icon-button:hover {
    background: var(--raised-hover);
    color: var(--text);
  }
  .icon-button[aria-pressed="true"] {
    background: var(--raised);
    color: var(--accent);
  }
  .icon-button:disabled {
    opacity: 0.45;
    cursor: default;
  }
</style>
