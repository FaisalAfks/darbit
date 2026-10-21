<!-- A glass panel. -->
<script lang="ts">
  import type { Snippet } from "svelte";

  let { children }: { children: Snippet } = $props();
</script>

<section class="card appear">{@render children()}</section>

<style>
  .card {
    background: var(--glass); backdrop-filter: blur(var(--blur)); border: 1px solid var(--line);
    border-radius: var(--radius-l); box-shadow: var(--shadow); padding: var(--space-3) var(--space-4);
  }
</style>
