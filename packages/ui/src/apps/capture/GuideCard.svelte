<!-- The setup guide card: the screen to open, the next thing to take, and progress. Hides into its progress
     strip when the mouse is away. See docs/tasks/T12-setup-guide.md step 3. -->
<script lang="ts">
  import Button from "$lib/components/Button.svelte";
  import Chip from "$lib/components/Chip.svelte";
  import ProgressStrip from "$lib/components/ProgressStrip.svelte";
  import TextSlot from "$lib/components/TextSlot.svelte";

  interface Current { screen: string; screenSay: string; kind: "image" | "region" | "point"; name: string; say: string; listAt?: [number, number]; nextName?: string }
  let { current, done, total, hidden = false }: { current: Current | null; done: number; total: number; hidden?: boolean } = $props();
</script>

<div class="guide" class:hidden>
  {#if current}
    <header>
      <b>{current.screen}</b>
      <span class="num">{done} / {total}</span>
    </header>
    <TextSlot slot="guide" text={current.screenSay} />
    <div class="item">
      <Chip tone={current.kind} text={current.kind} />
      <span class="name">{current.name}</span>
      {#if current.listAt}<span class="num list">{current.listAt[0]} / {current.listAt[1]} · next {current.nextName}</span>{/if}
    </div>
    <TextSlot slot="guide" text={current.say} />
    <footer>
      <Button action="capture.freeze" label="Capture" variant="primary" />
      <Button action="capture.previous" label="Back" />
      <Button action="capture.next" label="Skip" />
    </footer>
  {/if}
  <ProgressStrip {done} {total} />
</div>

<style>
  .guide {
    position: fixed; top: var(--space-3); left: 50%; translate: -50% 0; width: min(420px, 92vw);
    display: grid; gap: var(--space-2); padding: var(--space-3);
    background: var(--glass); backdrop-filter: blur(var(--blur)); border: 1px solid var(--line);
    border-radius: var(--radius-l); box-shadow: var(--shadow);
    transition: translate var(--move) var(--spring), opacity var(--fast) var(--ease);
  }
  .hidden { translate: -50% calc(-100% + 10px); }
  header { display: flex; justify-content: space-between; font: 600 var(--size-s) var(--font-strong); }
  header span, .list { color: var(--muted); font-size: var(--size-xs); }
  .item { display: flex; align-items: center; gap: var(--space-2); }
  .name { font-weight: 600; }
  footer { display: flex; gap: var(--space-2); }
</style>
