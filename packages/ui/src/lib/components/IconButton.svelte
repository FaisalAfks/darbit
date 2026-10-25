<!-- A round icon button for toolbars: same as Button, with an icon, and its label and keys on hover. -->
<script lang="ts">
  import { run } from "$lib/actions";
  import { keysFor } from "$lib/keymap";
  import Keycap from "./Keycap.svelte";

  let { action, label, icon, active = false }:
    { action: string; label: string; icon: string; active?: boolean } = $props();
  const keys = $derived(keysFor(action));
</script>

<button class:active onclick={() => run(action)} aria-label={label} aria-pressed={active} aria-keyshortcuts={keys}>
  <span aria-hidden="true">{icon}</span>
  <span class="tip">{label}{#if keys}&nbsp;<Keycap {keys} />{/if}</span>
</button>

<style>
  button {
    position: relative; width: 32px; height: 32px; display: grid; place-items: center;
    border: 0; border-radius: var(--radius-pill); background: transparent; color: var(--muted);
    font-size: var(--size-m); cursor: pointer;
    transition: background var(--fast) var(--ease), color var(--fast) var(--ease);
  }
  button:hover { background: var(--raised-hover); color: var(--text); }
  button:focus-visible { outline: none; box-shadow: var(--glow); }
  .active { color: var(--accent); background: var(--raised); }
  .tip {
    position: absolute; bottom: calc(100% + 8px); left: 50%; translate: -50% 4px; white-space: nowrap;
    display: inline-flex; align-items: center; gap: var(--space-1);
    padding: 3px 8px; border-radius: var(--radius-s); background: var(--glass-strong); color: var(--text);
    font-size: var(--size-xs); opacity: 0; pointer-events: none;
    transition: opacity var(--fast) var(--ease), translate var(--fast) var(--ease);
  }
  button:hover .tip { opacity: 1; translate: -50% 0; }
</style>
