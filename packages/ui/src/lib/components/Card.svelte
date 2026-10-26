<!-- A glass panel. -->
<script lang="ts">
  import type { Snippet } from "svelte";

  let { children }: { children: Snippet } = $props();
</script>

<section class="card appear">{@render children()}</section>

<style>
  .card {
    background: var(--glass); backdrop-filter: blur(var(--blur)); border: 1px solid var(--line);
    border-radius: var(--radius-xl); box-shadow: var(--shadow); padding: var(--space-m) var(--space-l);
  }
</style>
