<!-- Rows with a status dot, a name, a detail and an optional chip: Today's round, Watching, a bot's modes.
     <StatusList label="Watching" items={[{ name: "Disconnected", detail: "fired 0 times today", status: "ok" }]} /> -->
<script lang="ts">
  import Chip, { type Tone } from "./Chip.svelte";

  export interface Row {
    name: string;
    detail?: string;
    status: "ok" | "bad" | "now" | "idle";
    chip?: { text: string; tone?: Tone };
  }

  let { items, label }: { items: Row[]; label: string } = $props();
</script>

<ul class="list" aria-label={label}>
  {#each items as row (row.name)}
    <li class:now={row.status === "now"}>
      <span class="dot" data-status={row.status} aria-label={row.status}></span>
      <b>{row.name}</b>
      <small>{row.detail ?? ""}</small>
      {#if row.chip}<Chip text={row.chip.text} tone={row.chip.tone} />{:else}<span></span>{/if}
    </li>
  {/each}
</ul>

<style>
  .list {
    list-style: none;
    margin: 0;
    padding: 0;
    display: grid;
    gap: var(--space-1);
  }
  li {
    display: grid;
    grid-template-columns: 14px auto 1fr auto;
    gap: 14px;
    align-items: center;
    padding: 10px var(--space-3);
    border-radius: var(--radius-m);
    font-size: var(--size-m);
  }
  li:hover {
    background: var(--raised);
  }
  .now {
    background: color-mix(in oklab, var(--accent) 12%, transparent);
  }
  b {
    font-weight: 600;
  }
  small {
    color: var(--muted);
    font-size: var(--size-s);
    text-align: right;
    min-width: 0;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }
  .dot {
    width: 10px;
    height: 10px;
    border-radius: 50%;
    background: var(--faint);
  }
  [data-status="ok"] {
    background: var(--ok);
  }
  [data-status="bad"] {
    background: var(--danger);
  }
  [data-status="now"] {
    background: var(--accent);
    box-shadow: 0 0 0 4px color-mix(in oklab, var(--accent) 25%, transparent);
  }
</style>
