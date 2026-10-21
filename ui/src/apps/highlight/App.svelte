<!-- Highlight: boxes and scores over the screen, click-through. See docs/tasks/T11-highlight.md. -->
<script lang="ts">
  import { on } from "$lib/api";
  import ScoreBadge from "$lib/components/ScoreBadge.svelte";

  interface Hit { name: string; box: { x: number; y: number; w: number; h: number }; score: number; verdict: "ok" | "risky" | "missing" }
  let hits: Hit[] = $state([]);
  let missing: string[] = $state([]);

  on("highlight.hit", (hit: Hit) => hits.push(hit));
  on("highlight.done", (data: { missing: string[] }) => (missing = data.missing));
  // TODO(T11): fade after `seconds` unless pinned; ctrl held makes boxes clickable (retake in capture)
</script>

{#each hits as hit (hit.name)}
  <div class="hit" data-verdict={hit.verdict} style:left="{hit.box.x}px" style:top="{hit.box.y}px"
       style:width="{hit.box.w}px" style:height="{hit.box.h}px">
    <span class="label">{hit.name} <ScoreBadge score={hit.score} verdict={hit.verdict} /></span>
  </div>
{/each}

{#if missing.length}
  <aside class="missing appear">not seen: {missing.length}<small>{missing.join(", ")}</small></aside>
{/if}

<style>
  .hit {
    position: fixed; border: 2px solid var(--c); border-radius: var(--radius-s); pointer-events: none;
    box-shadow: 0 0 12px color-mix(in srgb, var(--c) 50%, transparent);
    animation: pop var(--move) var(--spring) both;
  }
  [data-verdict="ok"] { --c: var(--ok); }
  [data-verdict="risky"] { --c: var(--warn); }
  [data-verdict="missing"] { --c: var(--danger); }
  .label {
    position: absolute; bottom: calc(100% + 4px); left: -2px; white-space: nowrap;
    display: inline-flex; gap: var(--space-1); align-items: center; padding: 1px 6px;
    font: 600 var(--size-xs) var(--font-strong); color: var(--text);
    background: var(--glass-strong); border-radius: var(--radius-s);
  }
  .missing {
    position: fixed; right: var(--space-4); top: var(--space-4); display: grid; max-width: 260px;
    padding: var(--space-2) var(--space-3); background: var(--glass); backdrop-filter: blur(var(--blur));
    border: 1px solid var(--line); border-radius: var(--radius-m); color: var(--danger); font-size: var(--size-s);
  }
  small { color: var(--muted); }
</style>
