<!-- A dashboard tile in the Studio's Overview (decision 0011): a glass card with a small title, optional
     header extras, and the line of code or darbit.toml it comes from, shown when the source toggle is on.
     <Tile title="Progress" span={4} source={'d.progress("Speed Raid this week", done, 133)'}>…</Tile> -->
<script lang="ts">
  import type { Snippet } from "svelte";

  let {
    title,
    span = 6,
    source,
    showSource = false,
    extra,
    children,
  }: {
    title: string;
    span?: number; // columns of 12
    source?: string;
    showSource?: boolean;
    extra?: Snippet;
    children: Snippet;
  } = $props();
</script>

<article class="tile" class:showing={showSource && source} style:--span={span} aria-label={title}>
  <h4>{title}<span class="grow"></span>{#if extra}{@render extra()}{/if}</h4>
  {@render children()}
  {#if showSource && source}<pre class="source">{source}</pre>{/if}
</article>

<style>
  .tile {
    grid-column: span var(--span);
    display: grid;
    gap: var(--space-4);
    align-content: start;
    min-width: 0;
    padding: var(--space-5);
    border-radius: 20px;
    background: var(--glass);
    backdrop-filter: blur(var(--blur));
    border: 1px solid var(--line);
    box-shadow: var(--shadow);
  }
  .showing {
    outline: 1px dashed color-mix(in oklab, var(--accent) 45%, transparent);
    outline-offset: 3px;
  }
  h4 {
    margin: 0;
    display: flex;
    align-items: center;
    gap: var(--space-2);
    font: 650 var(--size-xs) / 1.4 var(--font-strong);
    color: var(--muted);
    text-transform: uppercase;
    letter-spacing: 0.08em;
  }
  .grow {
    flex: 1;
  }
  .source {
    margin: 0;
    padding: var(--space-2) var(--space-3);
    border-radius: var(--radius-m);
    border: 1px dashed color-mix(in oklab, var(--accent) 55%, transparent);
    background: color-mix(in oklab, var(--accent) 10%, var(--glass-strong));
    color: var(--accent);
    font: var(--size-xs) / 1.6 var(--mono);
    white-space: pre-wrap;
  }
</style>
