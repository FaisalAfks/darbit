<!-- A key as a small cap: "ctrl+alt+c" shows Ctrl Alt C. -->
<script lang="ts">
  let { keys }: { keys: string } = $props();
  const names: Record<string, string> = {
    ctrl: "Ctrl", alt: "Alt", shift: "Shift", enter: "⏎", esc: "Esc", tab: "Tab", space: "Space",
    arrows: "↑↓←→", delete: "Del", pagedown: "PgDn", pageup: "PgUp",
  };
  const parts = $derived(keys.split("+").map((k) => names[k] ?? k.toUpperCase()));
</script>

<span class="keys">{#each parts as part}<kbd>{part}</kbd>{/each}</span>

<style>
  .keys { display: inline-flex; gap: 2px; }
  kbd {
    font: 600 var(--size-xs) / 1.5 var(--font-strong);
    padding: 0 5px; min-width: 18px; text-align: center;
    border: 1px solid var(--line); border-bottom-width: 2px; border-radius: var(--radius-s);
    background: var(--raised); color: var(--text);
  }
</style>
