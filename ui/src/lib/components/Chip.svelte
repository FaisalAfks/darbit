<!-- A small label: a kind, a status, a link. -->
<script lang="ts">
  import type { Snippet } from "svelte";

  let { tone = "neutral", children }:
    { tone?: "neutral" | "image" | "region" | "point" | "ok" | "warn" | "danger"; children: Snippet } = $props();
</script>

<span class="chip" data-tone={tone}>{@render children()}</span>

<style>
  .chip {
    --c: var(--muted);
    display: inline-flex; align-items: center; gap: var(--space-1); padding: 2px 8px;
    border-radius: var(--radius-pill); font: 600 var(--size-xs) / 1.5 var(--font-strong);
    color: var(--c); background: color-mix(in srgb, var(--c) 14%, transparent);
    border: 1px solid color-mix(in srgb, var(--c) 30%, transparent);
  }
  [data-tone="image"] { --c: var(--kind-image); }
  [data-tone="region"] { --c: var(--kind-region); }
  [data-tone="point"] { --c: var(--kind-point); }
  [data-tone="ok"] { --c: var(--ok); }
  [data-tone="warn"] { --c: var(--warn); }
  [data-tone="danger"] { --c: var(--danger); }
</style>
