<!-- The recorder bar: one pill at the top, never takes focus from the game. See docs/tasks/T15-recorder.md. -->
<script lang="ts">
  import { on } from "$lib/api";
  import IconButton from "$lib/components/IconButton.svelte";

  let seconds = $state(0);
  let checkpoints = $state(0);
  let paused = $state(false);
  let name = $state(new URLSearchParams(location.search).get("run") ?? "run");

  on("record.tick", (t: { seconds: number; checkpoints: number; paused: boolean }) => {
    seconds = t.seconds;
    checkpoints = t.checkpoints;
    paused = t.paused;
  });
  const clock = $derived(`${Math.floor(seconds / 60).toString().padStart(2, "0")}:${Math.floor(seconds % 60).toString().padStart(2, "0")}`);
  // TODO(T15): register record.mark / run.pause / record.toggle actions that send record.* requests
</script>

<div class="bar appear" class:paused>
  <i class="dot"></i>
  <span class="num">{clock}</span>
  <span class="name">{name}</span>
  <span class="cp num">◆ {checkpoints}</span>
  <IconButton action="record.mark" label="Checkpoint" icon="◆" />
  <IconButton action="run.pause" label={paused ? "Resume" : "Pause"} icon={paused ? "▶" : "❚❚"} />
  <IconButton action="record.toggle" label="Stop" icon="■" />
</div>

<style>
  .bar {
    display: inline-flex; align-items: center; gap: var(--space-2); padding: 4px 6px 4px 14px; max-width: 360px;
    background: var(--glass); backdrop-filter: blur(var(--blur)); border: 1px solid var(--line);
    border-radius: var(--radius-pill); box-shadow: var(--shadow); font-size: var(--size-s);
  }
  .dot { width: 9px; height: 9px; border-radius: 50%; background: var(--danger); animation: pulse 1.6s ease-in-out infinite; }
  .paused .dot { background: var(--warn); animation: none; }
  .name { font-weight: 600; }
  .cp { color: var(--muted); font-size: var(--size-xs); }
</style>
