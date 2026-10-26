<!-- The Overview page: what the bot is doing now and how today is going, in blocks of rows (decision 0013,
     round 6). The bot's author sets the blocks and their order ([studio] tiles); anyone can rearrange, resize or
     hide them in Customize mode, saved on this PC per bot (the studio.overview:<bot> UI setting). -->
<script lang="ts">
  import { request } from "$lib/api";
  import { toast } from "$lib/toasts.svelte";
  import { clock, inTime } from "./time";
  import type { TileData } from "./TileView.svelte";

  interface Place {
    kind: string;
    size: "full" | "half";
    hidden: boolean;
  }

  let {
    bot,
    tiles,
    running,
    onsetup,
    onretake,
  }: { bot: string; tiles: TileData[]; running: string; onsetup: () => void; onretake: () => void } = $props();

  const NAMES: Record<string, string> = {
    now: "Now",
    round: "Today's round",
    progress: "Progress",
    gains: "Gains today",
    next: "Next up",
    activity: "What happened",
    failures: "Needs you",
    watching: "Watching",
    setup: "Setup",
  };
  const FULL = new Set(["now", "failures", "setup"]);

  let saved: Place[] = $state([]);
  let customizing = $state(false);
  let dragging: string | null = $state(null);
  let over: string | null = $state(null);

  const key = $derived(`studio.overview:${bot}`);
  const byKind = $derived(Object.fromEntries(tiles.map((tile) => [tile.kind, tile])) as Record<string, TileData>);
  const layout = $derived(arrange(tiles, saved));
  const shown = $derived(layout.filter((place) => !place.hidden && byKind[place.kind]));
  const hidden = $derived(layout.filter((place) => place.hidden && byKind[place.kind]));

  function arrange(current: TileData[], places: Place[]): Place[] {
    const result: Place[] = [];
    const seen = new Set<string>();
    for (const place of places) {
      if (seen.has(place.kind)) continue;
      seen.add(place.kind);
      result.push(place);
    }
    for (const tile of current) {
      if (seen.has(tile.kind)) continue;
      seen.add(tile.kind);
      result.push({ kind: tile.kind, size: FULL.has(tile.kind) ? "full" : "half", hidden: false });
    }
    if (!places.length) result.sort(alertsFirst); // by default, what needs you sits right under Now
    return result;
  }

  function alertsFirst(a: Place, b: Place): number {
    return rank(a.kind) - rank(b.kind);
  }

  function rank(kind: string): number {
    if (kind === "now") return 0;
    if (kind === "failures" || kind === "setup") return 1;
    return 2;
  }

  function number(value: number | null): string {
    if (value === null || value === undefined) return "";
    return value.toLocaleString("en").replace(/,/g, " ");
  }

  function save(next: Place[]): void {
    saved = next;
    request("settings.set", { key, value: next }).catch((error: Error) => toast(error.message));
  }

  function toggleSize(kind: string): void {
    save(layout.map((place) => (place.kind === kind ? { ...place, size: place.size === "full" ? "half" : "full" } : place)));
  }

  function toggleHidden(kind: string): void {
    save(layout.map((place) => (place.kind === kind ? { ...place, hidden: !place.hidden } : place)));
  }

  function drop(target: string): void {
    if (!dragging || dragging === target) return;
    const next = layout.filter((place) => place.kind !== dragging);
    const moved = layout.find((place) => place.kind === dragging)!;
    next.splice(next.findIndex((place) => place.kind === target), 0, moved);
    save(next);
    dragging = null;
    over = null;
  }

  function reset(): void {
    save([]);
    toast("Back to the bot's own layout");
  }

  function stateOf(step: Record<string, any>): string {
    if (step.state === "running") return "now";
    if (step.state === "ok") return "ok";
    if (step.state === "failed") return "bad";
    return "idle";
  }

  function pathTitle(tile: TileData): string[] {
    return tile.data.path ?? [];
  }

  $effect(() => {
    key;
    request("settings.get", { key })
      .then((value) => (saved = Array.isArray(value) ? value : []))
      .catch(() => (saved = []));
  });
</script>

<div class="overview">
  <div class="tools">
    {#if customizing}
      <span class="hint">Drag blocks to reorder · ½ resizes · 👁 hides</span>
      <span class="grow"></span>
      <button class="tool" onclick={reset}>Reset to the bot's layout</button>
      <button class="tool primary" onclick={() => (customizing = false)}>Done</button>
    {:else}
      <span class="grow"></span>
      <button class="tool" onclick={() => (customizing = true)}>⊞ Customize</button>
    {/if}
  </div>

  <div class="blocks" class:customizing>
    {#each shown as place (place.kind)}
      {@const tile = byKind[place.kind]}
      <section
        class="block"
        class:full={place.size === "full"}
        class:over={over === place.kind}
        class:lifted={dragging === place.kind}
        draggable={customizing}
        ondragstart={() => (dragging = place.kind)}
        ondragover={(event) => {
          if (!customizing) return;
          event.preventDefault();
          over = place.kind;
        }}
        ondragleave={() => (over = null)}
        ondrop={() => drop(place.kind)}
        ondragend={() => {
          dragging = null;
          over = null;
        }}
        aria-label={NAMES[place.kind] ?? tile.title}
      >
        {#if customizing}
          <div class="handle">
            <span class="grip" aria-hidden="true">⋮⋮</span><b>{NAMES[place.kind] ?? tile.title}</b><span class="grow"></span>
            <button aria-label="Change width" onclick={() => toggleSize(place.kind)}>{place.size === "full" ? "½" : "⬌"}</button>
            <button aria-label="Hide" onclick={() => toggleHidden(place.kind)}>👁</button>
          </div>
        {/if}

        {#if place.kind === "now"}
          <div class="now">
            <small>Now{running === "running" ? " · running" : running === "paused" ? " · paused" : ""}</small>
            {#if pathTitle(tile).length}
              <div class="crumb">
                {#each pathTitle(tile) as part, index (index)}{#if index}<span class="sep" aria-hidden="true">›</span>{/if}<span class:last={index === pathTitle(tile).length - 1}>{part}</span>{/each}
              </div>
              <span class="muted">since {clock(tile.data.since)}</span>
            {:else}
              <div class="crumb quiet">Not running</div>
              <span class="muted">Press ▶ to start it, or start it from a terminal: this page follows it either way.</span>
            {/if}
          </div>
        {:else if place.kind === "failures"}
          {@const last = tile.data.items[0]}
          <div class="needs">
            <span class="mark" aria-hidden="true">!</span>
            <span><b>{String(last.step).split(" > ").pop()}: {last.reason}</b><small>{tile.data.items.length > 1 ? `${tile.data.items.length} failures today, last at ${clock(last.time)}` : `at ${clock(last.time)}`}</small></span>
            <button class="tool primary" onclick={onretake}>▣ Retake</button>
          </div>
        {:else if place.kind === "setup"}
          {#if tile.data.error}
            <div class="needs"><span class="mark" aria-hidden="true">!</span><span><b>The setup guide has a mistake</b><small>{tile.data.error}</small></span></div>
          {:else if tile.data.done < tile.data.total}
            <div class="setup">
              <span class="cam" aria-hidden="true">▣</span>
              <span><b>{tile.data.total - tile.data.done} picture{tile.data.total - tile.data.done > 1 ? "s" : ""} to take before the bot can run</b><small>{tile.data.current ? `Next: ${tile.data.current.name} on ${tile.data.current.screen}` : "The guide shows each screen to open and what to box."}</small></span>
              <button class="tool primary" onclick={onsetup}>Start setup</button>
            </div>
          {:else}
            <div class="rows"><div class="row"><span class="dot ok"></span><b>Setup done</b><span class="right">all {tile.data.total} pictures taken</span></div></div>
          {/if}
        {:else}
          <h3>{NAMES[place.kind] ?? tile.title}</h3>
          <div class="rows">
            {#if place.kind === "round"}
              {#each tile.data.steps as step (step.name)}
                <div class="row" class:current={step.state === "running"}>
                  <span class="dot {stateOf(step)}"></span><b>{step.name}</b>
                  <span class="right">{#if step.state === "planned"}later{:else if step.state === "running"}<em>running</em>{:else if step.state === "failed"}<span class="bad">{step.reason ?? "failed"}</span>{:else}{clock(step.started)}{step.seconds ? ` · ${Math.round(step.seconds / 60)} m` : ""}{/if}</span>
                </div>
              {/each}
            {:else if place.kind === "next"}
              {#each tile.data.items as item (item.label)}
                <div class="row"><span class="icon" aria-hidden="true">⏱</span><b>{item.label}</b><span class="right"><em>in {inTime(item.in_seconds)}</em></span></div>
              {/each}
            {:else if place.kind === "progress"}
              {#each tile.data.items as item (item.label)}
                <div class="row">
                  <span class="icon" aria-hidden="true">✓</span><b>{item.label}</b>
                  <span class="right"><span class="bar"><i style:width="{Math.min(100, (item.done / item.total) * 100)}%"></i></span>{item.done} / {item.total}</span>
                </div>
              {/each}
            {:else if place.kind === "gains"}
              {#each tile.data.items as item (item.name)}
                <div class="row"><span class="icon" aria-hidden="true">{item.icon ?? "◆"}</span><b>{item.name}</b><span class="right"><span class="plus">+{number(item.today)}</span>{item.total !== null ? ` · ${number(item.total)}` : ""}</span></div>
              {/each}
            {:else if place.kind === "activity"}
              {#each tile.data.items.slice(0, 8) as item, index (index)}
                <div class="row log"><time>{clock(item.time)}</time><span>{item.event}{Object.keys(item.fields ?? {}).length ? " · " + Object.entries(item.fields).map(([name, value]) => `${name} ${value}`).join(", ") : ""}</span></div>
              {/each}
            {:else if place.kind === "watching"}
              {#each tile.data.items as item (item.name)}
                <div class="row"><span class="dot {item.state === 'watching' ? 'ok' : 'idle'}"></span><b>{item.name}</b><span class="right">{item.fired ? `fired ${item.fired}×, last ${clock(item.last_fired)}` : "not fired today"}</span></div>
              {/each}
            {/if}
          </div>
        {/if}
      </section>
    {/each}
  </div>

  {#if customizing && hidden.length}
    <div class="hidden-tray">
      <span class="hint">Hidden:</span>
      {#each hidden as place (place.kind)}
        <button class="tool" onclick={() => toggleHidden(place.kind)}>＋ {NAMES[place.kind] ?? place.kind}</button>
      {/each}
    </div>
  {/if}
</div>

<style>
  .overview {
    display: grid;
    gap: var(--space-m);
  }
  .tools,
  .hidden-tray {
    display: flex;
    align-items: center;
    gap: var(--space-s);
    min-height: var(--control-m);
  }
  .grow {
    flex: 1;
  }
  .hint {
    color: var(--muted);
    font-size: var(--size-caption);
  }
  .tool {
    height: var(--control-m);
    padding: 0 var(--space-l);
    border: 0;
    border-radius: var(--radius-pill);
    background: var(--raised);
    color: var(--text);
    font: 600 var(--size-caption) / 1 var(--font-strong);
    cursor: pointer;
    white-space: nowrap;
    transition: background var(--duration-fast) var(--curve-easy-ease);
  }
  .tool:hover {
    background: var(--raised-hover);
  }
  .tool.primary {
    background: var(--accent);
    color: var(--on-accent);
  }
  .blocks {
    display: grid;
    grid-template-columns: 1fr 1fr;
    grid-auto-flow: dense;
    gap: var(--space-m);
    align-items: start;
  }
  .block {
    display: grid;
    gap: var(--space-s);
    padding: var(--space-l) var(--space-xl);
    border-radius: var(--radius-xl);
    background: var(--glass);
    border: 1px solid var(--line);
    animation: rise var(--duration-normal) var(--curve-decelerate) both;
    transition:
      transform var(--duration-normal) var(--curve-decelerate),
      box-shadow var(--duration-normal) var(--curve-decelerate),
      opacity var(--duration-fast) var(--curve-easy-ease);
  }
  .block.full {
    grid-column: 1 / -1;
  }
  .customizing .block {
    cursor: grab;
    border-style: dashed;
  }
  .block.lifted {
    opacity: 0.4;
  }
  .block.over {
    box-shadow: 0 0 0 2px var(--accent), 0 0 var(--space-xl) color-mix(in oklab, var(--accent) 35%, transparent);
    transform: scale(1.01);
  }
  .handle {
    display: flex;
    align-items: center;
    gap: var(--space-s);
    margin: calc(-1 * var(--space-s)) calc(-1 * var(--space-m)) var(--space-xs);
    padding: var(--space-xs) var(--space-s);
    border-radius: var(--radius-m);
    background: var(--raised);
    font-size: var(--size-caption);
  }
  .handle .grip {
    color: var(--faint);
  }
  .handle button {
    width: var(--control-s);
    height: var(--control-s);
    border: 0;
    border-radius: var(--radius-m);
    background: none;
    color: var(--text);
    cursor: pointer;
  }
  .handle button:hover {
    background: var(--raised-hover);
  }
  h3 {
    margin: 0;
    font: 700 var(--size-caption) / 1 var(--font-strong);
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: var(--muted);
  }
  .now {
    display: grid;
    gap: var(--space-xs);
  }
  .now small {
    font: 700 var(--size-caption) / 1 var(--font-strong);
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: var(--muted);
  }
  .crumb {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: var(--space-m);
    font: 700 var(--size-title) / var(--line-title) var(--font-strong);
  }
  .crumb.quiet {
    color: var(--muted);
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
  .needs,
  .setup {
    display: grid;
    grid-template-columns: auto 1fr auto;
    gap: var(--space-m);
    align-items: center;
  }
  .needs > span:nth-child(2),
  .setup > span:nth-child(2) {
    display: grid;
  }
  .needs small,
  .setup small {
    color: var(--muted);
    font-size: var(--size-caption);
  }
  .block:has(.needs) {
    background: linear-gradient(90deg, color-mix(in oklab, var(--danger) 14%, var(--glass)), var(--glass));
    border-color: color-mix(in oklab, var(--danger) 30%, transparent);
  }
  .block:has(.setup) {
    background: linear-gradient(90deg, color-mix(in oklab, var(--warn) 14%, var(--glass)), var(--glass));
    border-color: color-mix(in oklab, var(--warn) 30%, transparent);
  }
  .mark,
  .cam {
    width: var(--control-m);
    height: var(--control-m);
    display: grid;
    place-items: center;
    border-radius: 50%;
    font-weight: 800;
  }
  .mark {
    background: color-mix(in oklab, var(--danger) 22%, transparent);
    color: var(--danger);
  }
  .cam {
    background: color-mix(in oklab, var(--warn) 22%, transparent);
    color: var(--warn);
  }
  .rows {
    display: grid;
  }
  .row {
    display: grid;
    grid-template-columns: var(--control-s) 1fr auto;
    gap: var(--space-m);
    align-items: center;
    padding: var(--space-s) var(--space-xs);
    border-top: 1px solid var(--line);
  }
  .row:first-child {
    border-top: 0;
  }
  .row.current {
    margin: 0 calc(-1 * var(--space-s));
    padding: var(--space-s) var(--space-m);
    border-radius: var(--radius-m);
    background: color-mix(in oklab, var(--accent) 12%, transparent);
  }
  .row b {
    font-weight: 600;
  }
  .row.log {
    grid-template-columns: calc(2 * var(--control-m)) 1fr;
    font-size: var(--size-body);
  }
  .row.log time {
    font-family: var(--mono);
    color: var(--faint);
  }
  .right {
    display: flex;
    align-items: center;
    gap: var(--space-m);
    color: var(--muted);
    font-size: var(--size-body);
  }
  .right em {
    font-style: normal;
    color: var(--accent);
    font-weight: 700;
  }
  .bad {
    color: var(--danger);
  }
  .plus {
    color: var(--ok);
    font-weight: 700;
  }
  .icon {
    text-align: center;
    color: var(--muted);
  }
  .dot {
    width: var(--space-m-nudge);
    height: var(--space-m-nudge);
    border-radius: 50%;
    justify-self: center;
    background: var(--faint);
  }
  .dot.ok {
    background: var(--ok);
  }
  .dot.bad {
    background: var(--danger);
  }
  .dot.now {
    background: var(--accent);
    box-shadow: 0 0 0 var(--space-xs) color-mix(in oklab, var(--accent) 22%, transparent);
  }
  .bar {
    display: block;
    width: calc(4 * var(--control-m));
    height: var(--space-s);
    border-radius: var(--radius-pill);
    background: var(--raised);
    overflow: hidden;
  }
  .bar i {
    display: block;
    height: 100%;
    background: linear-gradient(90deg, var(--accent), var(--accent-2));
  }
  @keyframes rise {
    from {
      opacity: 0;
      transform: translateY(var(--space-xs));
    }
    to {
      opacity: 1;
      transform: none;
    }
  }
</style>
