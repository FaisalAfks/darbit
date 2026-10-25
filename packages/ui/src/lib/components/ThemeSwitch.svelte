<!-- Cycles the themes, like ctrl+alt+t. -->
<script lang="ts">
  import { cycleTheme } from "$lib/theme";

  let name = $state(document.documentElement.dataset.theme ?? "glass-dark");
</script>

<button onclick={() => (name = cycleTheme())} title="Theme (ctrl+alt+t)">◐ {name}</button>

<style>
  button {
    border: 1px solid var(--line); border-radius: var(--radius-pill); background: var(--raised);
    color: var(--muted); padding: 3px 10px; font-size: var(--size-xs); cursor: pointer;
  }
  button:hover { color: var(--text); }
</style>
