<!-- The run pill: darbit Studio while a bot runs, in a small bar at the top of the screen (desktop/pill.py,
     issue 130). The bot, what it's doing now, Pause, Stop and back to the Studio. -->
<script lang="ts">
  import { on, request } from "$lib/api";
  import IconButton from "$lib/components/IconButton.svelte";
  import Pill from "$lib/components/Pill.svelte";

  let { path }: { path: string } = $props();

  let name = $state("");
  let status = $state("running");
  let now: string[] = $state([]);

  async function load(): Promise<void> {
    const overview = await request("dashboard.tiles", { path });
    name = overview.project.name;
    status = overview.project.status;
    const tile = overview.tiles.find((each: { kind: string }) => each.kind === "now");
    now = tile ? tile.data.path : [];
  }

  function pause(): void {
    request("project.pause", { path }).then((reply) => (status = reply.status));
  }

  function stop(): void {
    status = "stopping";
    request("project.stop", { path });
  }

  function expand(): void {
    request("studio.expand");
  }

  $effect(() => {
    load();
    const stopStatus = on("project.status", (data) => {
      if (data.path === path) status = data.status;
    });
    const stopChanged = on("project.changed", (data) => {
      if (data.path === path) load();
    });
    return () => {
      stopStatus();
      stopChanged();
    };
  });
</script>

<div class="bar">
  <Pill label="Run pill">
    <span class="what" class:held={status === "paused"}>
      <span class="dot"></span>
      <b>{name}</b>
      <span class="now">{status === "paused" ? "Paused" : now.length ? now.join(" › ") : "Starting"}</span>
    </span>
    <IconButton label={status === "paused" ? "Resume" : "Pause"} icon={status === "paused" ? "▶" : "❚❚"} onclick={pause} disabled={status === "stopping"} />
    <IconButton label="Stop" icon="■" onclick={stop} disabled={status === "stopping"} />
    <IconButton label="Back to darbit Studio" icon="⤢" onclick={expand} />
  </Pill>
</div>

<style>
  :global(html),
  :global(body) {
    background: transparent;
  }
  .bar {
    display: grid;
    place-items: center;
    height: 100vh;
  }
  .what {
    display: inline-flex;
    align-items: center;
    gap: var(--space-s-nudge);
    max-width: var(--width-tooltip);
    padding: 0 var(--space-s-nudge) 0 var(--space-m);
    font-size: var(--size-caption);
    color: var(--muted);
    white-space: nowrap;
  }
  .what b {
    color: var(--text);
  }
  .now {
    overflow: hidden;
    text-overflow: ellipsis;
  }
  .dot {
    flex: none;
    width: var(--space-s);
    height: var(--space-s);
    border-radius: 50%;
    background: var(--ok);
  }
  .held .dot {
    background: var(--warn);
  }
</style>
