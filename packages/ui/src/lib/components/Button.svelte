<!-- A button that runs a named action (its keys show in the tooltip), or its own onclick.
     <Button action="run.pause" label="Pause" icon="❚❚" />   <Button label="Save" variant="primary" onclick={save} /> -->
<script lang="ts">
  import { run } from "$lib/actions";
  import { keysFor } from "$lib/keymap";
  import { tip } from "$lib/tooltip";

  let {
    label,
    action,
    onclick,
    icon,
    variant = "default",
    size = "m",
    disabled = false,
  }: {
    label: string;
    action?: string;
    onclick?: () => void;
    icon?: string;
    variant?: "default" | "primary" | "danger" | "quiet";
    size?: "m" | "s";
    disabled?: boolean;
  } = $props();

  const keys = $derived(action ? keysFor(action) : undefined);

  function press(): void {
    if (onclick) onclick();
    else if (action) run(action);
  }
</script>

<button
  class="button"
  data-variant={variant}
  data-size={size}
  {disabled}
  onclick={press}
  aria-keyshortcuts={keys}
  use:tip={{ label, keys }}
>
  {#if icon}<span class="icon" aria-hidden="true">{icon}</span>{/if}{label}
</button>

<style>
  .button {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    gap: var(--space-s);
    min-height: var(--control-m);
    padding: 0 var(--space-l);
    border: 0;
    border-radius: var(--radius-m);
    background: var(--raised);
    color: var(--text);
    font: 600 var(--size-body) / 1 var(--font-strong);
    white-space: nowrap;
    cursor: pointer;
    transition:
      background var(--duration-fast) var(--curve-easy-ease),
      transform var(--duration-fast) var(--curve-easy-ease);
  }
  .button:hover {
    background: var(--raised-hover);
  }
  .button:active {
    transform: scale(0.97);
  }
  .button:disabled {
    opacity: 0.45;
    cursor: default;
    transform: none;
  }
  [data-size="s"] {
    min-height: var(--control-s);
    padding: 0 var(--space-m);
    font-size: var(--size-caption);
  }
  [data-variant="primary"] {
    background: var(--accent);
    color: var(--on-accent);
  }
  [data-variant="primary"]:hover {
    background: color-mix(in oklab, var(--accent) 88%, var(--text));
  }
  [data-variant="danger"] {
    color: var(--danger);
  }
  [data-variant="quiet"] {
    background: transparent;
    color: var(--muted);
  }
  [data-variant="quiet"]:hover {
    color: var(--text);
  }
  .icon {
    font-size: 1.05em;
  }
</style>
