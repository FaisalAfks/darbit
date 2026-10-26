<!-- The messages from toast() (lib/toasts.svelte.ts): one line, coloured by its slot, gone after 3 s, never
     takes focus. At most three stack. Put one in each window. -->
<script lang="ts">
  import { messages } from "$lib/toasts.svelte";
  import TextSlot from "./TextSlot.svelte";
</script>

<div class="toasts" aria-live="polite">
  {#each messages as message (message.id)}
    <div class="toast appear"><TextSlot slot={message.slot} text={message.text} from={message.from} /></div>
  {/each}
</div>

<style>
  .toasts {
    position: fixed;
    z-index: 60;
    right: var(--space-4);
    bottom: var(--space-4);
    display: grid;
    gap: var(--space-2);
    pointer-events: none;
  }
  .toast {
    max-width: 380px;
    padding: var(--space-3) var(--space-4);
    border-radius: var(--radius-m);
    background: var(--glass-strong);
    backdrop-filter: blur(var(--blur));
    border: 1px solid var(--line);
    box-shadow: var(--shadow);
  }
</style>
