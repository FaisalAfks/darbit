<!-- Text from darbit (tool), a bot (bot) or a guide's author (guide), each styled so it's clear who's talking.
     One line, cut with "…", in full on hover or focus. Text only, never HTML. -->
<script lang="ts">
  let { slot, text, from }: { slot: "tool" | "bot" | "guide"; text: string; from?: string } = $props();
</script>

<p class="slot" data-slot={slot} title={text}>
  {#if slot === "bot" && from}<b>{from}</b>{/if}
  <span>{text}</span>
</p>

<style>
  .slot {
    margin: 0;
    display: flex;
    gap: var(--space-s);
    align-items: baseline;
    min-width: 0;
  }
  span {
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }
  .slot:hover span,
  .slot:focus-within span {
    white-space: normal;
  }
  [data-slot="tool"] {
    color: var(--slot-tool);
    font-size: var(--size-caption);
  }
  [data-slot="guide"] {
    color: var(--slot-guide);
    font-size: var(--size-body);
  }
  [data-slot="bot"] {
    color: var(--slot-bot);
    font-size: var(--size-caption);
  }
  b {
    flex: none;
    font: 600 var(--size-caption) / 1.6 var(--font-strong);
    padding: 0 var(--space-s);
    border-radius: var(--radius-pill);
    background: color-mix(in oklab, var(--slot-bot) 18%, transparent);
  }
</style>
