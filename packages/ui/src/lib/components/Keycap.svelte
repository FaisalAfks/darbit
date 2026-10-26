<!-- Keys as small caps: "ctrl+alt+c" shows Ctrl Alt C. `down` lights them, as when pressed. -->
<script lang="ts">
  import { keyNames } from "$lib/keys";

  let { keys, down = false }: { keys: string; down?: boolean } = $props();
  const parts = $derived(keyNames(keys));
</script>

<span class="keys" class:down aria-label={parts.join(" ")}>
  {#each parts as part, index (index)}<kbd>{part}</kbd>{/each}
</span>

<style>
  .keys {
    display: inline-flex;
    gap: 3px;
  }
  kbd {
    font: 600 var(--size-xs) / 1.6 var(--font-strong);
    padding: 0 6px;
    min-width: 20px;
    text-align: center;
    border: 1px solid var(--line);
    border-bottom-width: 2px;
    border-radius: var(--radius-s);
    background: var(--raised);
    color: var(--text);
    transition:
      transform var(--fast) var(--ease),
      background var(--fast) var(--ease);
  }
  .down kbd {
    background: var(--accent);
    color: var(--on-accent);
    transform: translateY(1px);
  }
</style>
