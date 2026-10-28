<!-- A glass pill holding controls: the Studio's bot switcher, run controls and tool buttons sit in these,
     the same shape as the capture toolbar and the recorder bar. <Pill label="Run controls">…</Pill> -->
<script lang="ts">
  import type { Snippet } from "svelte";

  let { label, children }: { label?: string; children: Snippet } = $props();
</script>

<div class="pill" role={label ? "group" : undefined} aria-label={label}>{@render children()}</div>

<style>
  .pill {
    display: inline-flex;
    align-items: center;
    gap: var(--space-xs);
    padding: var(--space-xs);
    border-radius: var(--radius-pill);
    background: var(--glass);
    border: 1px solid var(--line);
    box-shadow: var(--shadow);
    max-width: 100%;
  }
  .pill :global(hr) {
    width: 1px;
    height: var(--space-xl);
    margin: 0 var(--space-xs);
    border: 0;
    background: var(--line);
    flex: none;
  }
</style>
