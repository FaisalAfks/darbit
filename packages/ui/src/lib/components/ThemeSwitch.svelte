<!-- Cycles the themes, like ctrl+alt+t, and shows the current one (also when another window changed it). -->
<script lang="ts">
  import { currentTheme, cycleTheme, onThemeChange } from "$lib/theme";

  let name = $state(currentTheme());
  $effect(() => onThemeChange((now) => (name = now)));
</script>

<button onclick={() => cycleTheme()} title="Theme (ctrl+alt+t)" aria-label="Theme: {name}, change">◐ {name}</button>

<style>
  button {
    border: 1px solid var(--line); border-radius: var(--radius-pill); background: var(--raised);
    color: var(--muted); min-height: var(--control-s); padding: var(--space-xxs) var(--space-m-nudge); font-size: var(--size-caption); cursor: pointer;
  }
  button:hover { color: var(--text); }
</style>
