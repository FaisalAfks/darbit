<!-- One Overview tile from the server (server/dashboard.py): picks the components for its kind. -->
<script lang="ts">
  import Bar from "$lib/components/Bar.svelte";
  import Ring from "$lib/components/Ring.svelte";
  import StatusList, { type Row } from "$lib/components/StatusList.svelte";
  import Tile from "$lib/components/Tile.svelte";
  import { clock, inTime } from "./time";

  export interface TileData {
    kind: string;
    title: string;
    data: Record<string, any>;
  }

  const SOURCES: Record<string, string> = {
    now: 'with d.step("Speed Raid"):\n    with d.step(name): ...',
    round: "with d.step(mode.name): mode.play()   # top-level steps",
    progress: 'd.progress("Speed Raid this week", done, total)',
    next: 'd.next("Weekly reset", when)',
    activity: 'd.record("speed raid done", character=name)',
    failures: "a step that raised, with its screenshot",
    watching: 'd.observe(img.DISCONNECTED)',
    setup: "guide.toml and the pictures in assets/images",
  };
  const SPANS: Record<string, number> = { now: 8, progress: 4, round: 7, next: 5, activity: 7, watching: 5, failures: 6, setup: 6 };

  let { tile, showSource = false }: { tile: TileData; showSource?: boolean } = $props();

  function roundRows(steps: any[]): Row[] {
    const rows: Row[] = [];
    for (const step of steps) {
      let status: Row["status"] = "ok";
      if (step.state === "running") status = "now";
      else if (step.state === "failed") status = "bad";
      else if (step.state !== "ok") status = "idle";
      const seconds = step.seconds ? ` · ${Math.round(step.seconds / 60)} m` : "";
      rows.push({
        name: step.name,
        detail: `${clock(step.started)}${seconds}`,
        status,
        chip: { text: step.reason ?? step.state, tone: status === "bad" ? "danger" : status === "now" ? "info" : "ok" },
      });
    }
    return rows;
  }

  function watchingRows(items: any[]): Row[] {
    const rows: Row[] = [];
    for (const item of items) {
      const fired = item.fired ? `fired ${item.fired} time${item.fired > 1 ? "s" : ""}, last ${clock(item.last_fired)}` : "not fired today";
      rows.push({ name: item.name, detail: fired, status: item.state === "watching" ? "ok" : "idle", chip: { text: item.state, tone: "ok" } });
    }
    return rows;
  }
</script>

<Tile title={tile.title} span={SPANS[tile.kind] ?? 6} {showSource} source={SOURCES[tile.kind]}>
  {#if tile.kind === "now"}
    {#if tile.data.path.length}
      <div class="crumb">
        {#each tile.data.path as part, index (index)}
          {#if index}<span class="sep" aria-hidden="true">›</span>{/if}
          <span class:last={index === tile.data.path.length - 1}>{part}</span>
        {/each}
      </div>
      <span class="muted">since {clock(tile.data.since)}</span>
    {:else}
      <span class="muted">Not running. Press Run, or start the bot from a terminal: this page follows it either way.</span>
    {/if}
  {:else if tile.kind === "progress"}
    <div class="progress">
      {#each tile.data.items as item, index (item.label)}
        {#if index === 0}
          <Ring label={item.label} done={item.done} total={item.total} />
        {:else}
          <Bar label={item.label} done={item.done} total={item.total} />
        {/if}
      {/each}
    </div>
  {:else if tile.kind === "round"}
    <StatusList label={tile.title} items={roundRows(tile.data.steps)} />
  {:else if tile.kind === "next"}
    <ul class="next">
      {#each tile.data.items as item (item.label)}
        <li><b>{item.label}</b><em>{inTime(item.in_seconds)}</em></li>
      {/each}
    </ul>
  {:else if tile.kind === "watching"}
    <StatusList label={tile.title} items={watchingRows(tile.data.items)} />
  {:else if tile.kind === "activity" || tile.kind === "failures"}
    <ul class="events">
      {#each tile.data.items.slice(0, 12) as item, index (index)}
        <li class:bad={tile.kind === "failures"}>
          <time>{clock(item.time)}</time>
          <span>{tile.kind === "failures" ? `${item.step}: ${item.reason}` : `${item.event}${Object.keys(item.fields ?? {}).length ? " · " + Object.entries(item.fields).map(([key, value]) => `${key} ${value}`).join(", ") : ""}`}</span>
        </li>
      {/each}
    </ul>
  {:else if tile.kind === "setup"}
    {#if tile.data.error}
      <span class="bad">{tile.data.error}</span>
    {:else}
      <Bar label="Pictures taken" done={tile.data.done} total={tile.data.total} />
      {#if tile.data.current}<span class="muted">Next: {tile.data.current.name} on {tile.data.current.screen}</span>{/if}
    {/if}
  {/if}
</Tile>

<style>
  .crumb {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: var(--space-s);
    font: 700 var(--size-title3) / var(--line-title3) var(--font-strong);
  }
  .sep {
    color: var(--faint);
    font-weight: 400;
  }
  .last {
    color: var(--accent);
  }
  .muted {
    color: var(--muted);
    font-size: var(--size-body);
  }
  .bad {
    color: var(--danger);
  }
  .progress {
    display: grid;
    gap: var(--space-m);
    justify-items: stretch;
  }
  .next,
  .events {
    list-style: none;
    margin: 0;
    padding: 0;
    display: grid;
    gap: var(--space-s);
  }
  .next li {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: var(--space-m);
    padding: var(--space-m);
    border-radius: var(--radius-l);
    background: var(--raised);
  }
  .next em {
    font-style: normal;
    font: 700 var(--size-subtitle) / var(--line-subtitle) var(--font-strong);
    color: var(--accent);
  }
  .events li {
    display: grid;
    grid-template-columns: calc(6 * var(--space-s)) 1fr;
    gap: var(--space-m);
    font-size: var(--size-body);
  }
  .events time {
    font-family: var(--mono);
    color: var(--faint);
  }
</style>
