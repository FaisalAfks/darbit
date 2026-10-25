<!-- One line, coloured by its slot, gone after 3 s, never takes focus. At most three stack. -->
<script lang="ts">
  import TextSlot from "./TextSlot.svelte";

  type Item = { id: number; slot: "tool" | "bot" | "guide"; text: string; from?: string };
  let { toasts }: { toasts: Item[] } = $props();
</script>

<div class="toasts" aria-live="polite">
  {#each toasts.slice(-3) as toast (toast.id)}
    <div class="toast appear"><TextSlot slot={toast.slot} text={toast.text} from={toast.from} /></div>
  {/each}
</div>

<style>
  .toasts {
    position: fixed; right: var(--space-4); bottom: var(--space-4); display: grid; gap: var(--space-2);
    pointer-events: none;
  }
  .toast {
    padding: var(--space-2) var(--space-3); border-radius: var(--radius-m); max-width: 360px;
    background: var(--glass-strong); backdrop-filter: blur(var(--blur)); border: 1px solid var(--line);
    box-shadow: var(--shadow);
  }
</style>
