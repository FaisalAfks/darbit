<!-- A pill button that runs a named action; its keys show on hover. See docs/tasks/T03-components.md. -->
<script lang="ts">
  import type { Snippet } from "svelte";
  import { run } from "$lib/actions";
  import { keysFor } from "$lib/keymap";
  import Keycap from "./Keycap.svelte";

  let { action, label, primary = false, children }:
    { action: string; label: string; primary?: boolean; children?: Snippet } = $props();
  const keys = $derived(keysFor(action));
</script>

<button class:primary onclick={() => run(action)} title={label} aria-keyshortcuts={keys}>
  {#if children}{@render children()}{:else}{label}{/if}
  {#if keys}<span class="tip"><Keycap {keys} /></span>{/if}
</button>

<style>
  button {
    position: relative; display: inline-flex; align-items: center; gap: var(--space-2);
    padding: 6px 14px; border: 0; border-radius: var(--radius-pill);
    background: var(--raised); color: var(--text); font: 600 var(--size-s) / 1.2 var(--font-strong);
    cursor: pointer;
    transition: background var(--fast) var(--ease), box-shadow var(--fast) var(--ease), transform var(--fast) var(--ease);
  }
  button:hover { background: var(--raised-hover); }
  button:active { transform: scale(0.97); }
  button:focus-visible { outline: none; box-shadow: var(--glow); }
  .primary { background: var(--accent); color: var(--on-accent); }
  .tip {
    position: absolute; bottom: calc(100% + 6px); left: 50%; translate: -50% 4px;
    opacity: 0; pointer-events: none; transition: opacity var(--fast) var(--ease), translate var(--fast) var(--ease);
  }
  button:hover .tip { opacity: 1; translate: -50% 0; }
</style>
