<!-- Text from darbit (tool), a bot (bot) or a guide's author (guide), each styled so it's clear who's talking.
     One line, cut with "…", full on hover or focus. Text only, never HTML. -->
<script lang="ts">
  let { slot, text, from, image }:
    { slot: "tool" | "bot" | "guide"; text: string; from?: string; image?: string } = $props();
</script>

<p class="slot" data-slot={slot} title={text}>
  {#if slot === "bot" && from}<b>{from}</b>{/if}
  <span>{text}</span>
  {#if image}<img src={image} alt="" class="example" />{/if}
</p>

<style>
  .slot { margin: 0; display: flex; gap: var(--space-2); align-items: baseline; min-width: 0; position: relative; }
  span { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
  .slot:hover span { white-space: normal; }
  [data-slot="tool"] { color: var(--slot-tool); font-size: var(--size-xs); }
  [data-slot="guide"] { color: var(--slot-guide); font-size: var(--size-s); }
  [data-slot="bot"] { color: var(--slot-bot); font-size: var(--size-s); }
  b {
    flex: none; font: 600 var(--size-xs) / 1.6 var(--font-strong); padding: 0 6px; border-radius: var(--radius-pill);
    background: color-mix(in srgb, var(--slot-bot) 18%, transparent);
  }
  .example {
    position: absolute; top: calc(100% + 6px); left: 0; width: 220px; border-radius: var(--radius-m);
    box-shadow: var(--shadow); opacity: 0; pointer-events: none; transition: opacity var(--fast) var(--ease);
  }
  .slot:hover .example { opacity: 1; }
</style>
