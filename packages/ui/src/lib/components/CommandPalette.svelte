<!-- ctrl+k: every action in this window by name, with its keys. See docs/tasks/T03-components.md step 7. -->
<script lang="ts">
  import { available, run } from "$lib/actions";
  import { keysFor } from "$lib/keymap";
  import Keycap from "./Keycap.svelte";

  let { open = $bindable(false) }: { open?: boolean } = $props();
  let query = $state("");
  // TODO(T03): fuzzy matching, arrow keys to move, Enter runs, Esc closes
  const found = $derived(available().filter((a) => a.label.toLowerCase().includes(query.toLowerCase())));

  function choose(name: string) {
    run(name);
    open = false;
  }
</script>

{#if open}
  <div class="palette appear" role="dialog" aria-label="Commands">
    <input bind:value={query} placeholder="Type a command" />
    <ul>
      {#each found as action}
        {@const keys = keysFor(action.name)}
        <li><button onclick={() => choose(action.name)}>{action.label}{#if keys}<Keycap {keys} />{/if}</button></li>
      {/each}
    </ul>
  </div>
{/if}

<style>
  .palette {
    position: fixed; top: 18%; left: 50%; translate: -50% 0; width: min(480px, 90vw);
    background: var(--glass-strong); backdrop-filter: blur(var(--blur)); border: 1px solid var(--line);
    border-radius: var(--radius-l); box-shadow: var(--shadow); padding: var(--space-2);
  }
  input {
    width: 100%; padding: var(--space-2) var(--space-3); border: 0; border-radius: var(--radius-m);
    background: var(--raised); color: var(--text); font: inherit;
  }
  ul { list-style: none; margin: var(--space-2) 0 0; padding: 0; max-height: 300px; overflow: auto; }
  button {
    width: 100%; display: flex; justify-content: space-between; padding: 6px var(--space-3); border: 0;
    border-radius: var(--radius-s); background: none; color: var(--text); font: inherit; cursor: pointer;
  }
  button:hover { background: var(--raised-hover); }
</style>
