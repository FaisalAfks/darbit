<!-- The Studio's own settings, kept on this PC (ui.json): sections on the left, one form on the right.
     Each change is saved at once through `onchange(key, value)`. See decision 0013, round 6. -->
<script lang="ts">
  import Segmented from "$lib/components/Segmented.svelte";
  import Switch from "$lib/components/Switch.svelte";
  import { chooseTheme, THEMES, type ThemeName } from "$lib/theme";

  export interface StudioValues {
    theme: ThemeName;
    picker: string; // "dropdown" or "sidebar"
    effects: boolean;
    closing: string; // "tray" or "quit"
    collapseOnRun: boolean;
    pillHideAfter: string; // seconds, or "never"
  }

  let { values = $bindable(), onchange }: { values: StudioValues; onchange: (key: string, value: unknown) => void } = $props();

  const SECTIONS = [
    { value: "look", label: "Look", icon: "◐" },
    { value: "window", label: "Window", icon: "▢" },
    { value: "running", label: "While a bot runs", icon: "▶" },
    { value: "keys", label: "Keys", icon: "⌨" },
    { value: "about", label: "About", icon: "ⓘ" },
  ];
  const THEME_LABELS: Record<ThemeName, string> = {
    "glass-dark": "Glass dark",
    "glass-light": "Glass light",
    midnight: "Midnight",
    "high-contrast": "High contrast",
  };
  let section = $state("look");

  function pickTheme(event: Event): void {
    values.theme = (event.target as HTMLSelectElement).value as ThemeName;
    chooseTheme(values.theme);
  }

  function pickHide(event: Event): void {
    values.pillHideAfter = (event.target as HTMLSelectElement).value;
    onchange("studio.pill_hide_after", values.pillHideAfter === "never" ? 0 : Number(values.pillHideAfter));
  }
</script>

<div class="studio-settings">
  <nav class="sections" aria-label="Studio settings">
    <h2>Studio</h2>
    {#each SECTIONS as item (item.value)}
      <button class:on={section === item.value} onclick={() => (section = item.value)}><span aria-hidden="true">{item.icon}</span>{item.label}</button>
    {/each}
  </nav>
  <section class="form">
    {#if section === "look"}
      <h3>Look</h3>
      <p class="lead">How the Studio and its tools look on this PC.</p>
      <div class="row">
        <span><b>Theme</b><small>Every darbit window follows it.</small></span>
        <select value={values.theme} onchange={pickTheme}>
          {#each THEMES as name (name)}<option value={name}>{THEME_LABELS[name]}</option>{/each}
        </select>
      </div>
      <div class="row">
        <span><b>Bot picker</b><small>How you switch between bots.</small></span>
        <Segmented
          label="Bot picker"
          items={[{ value: "dropdown", label: "Dropdown" }, { value: "sidebar", label: "Sidebar" }]}
          bind:value={() => values.picker, (next) => { values.picker = next; onchange("studio.picker", next); }}
        />
      </div>
      <Switch label="Smooth effects" help="Glass and motion. Turn off on a slower PC; Windows' reduce-motion setting also does." bind:checked={values.effects} onchange={(on) => onchange("studio.effects", on)} />
    {:else if section === "window"}
      <h3>Window</h3>
      <p class="lead">How the Studio opens, closes and remembers itself.</p>
      <div class="row">
        <span><b>Closing the window</b><small>Keep running: the Studio hides to the tray icon, and a running bot keeps its pill.</small></span>
        <Segmented
          label="Closing the window"
          items={[{ value: "tray", label: "Keep running in the tray" }, { value: "quit", label: "Quit" }]}
          bind:value={() => values.closing, (next) => { values.closing = next; onchange("studio.closing", next); }}
        />
      </div>
      <div class="row muted"><span><b>Size and place</b><small>The Studio opens where you left it, on the same screen.</small></span><span class="tag">always on</span></div>
    {:else if section === "running"}
      <h3>While a bot runs</h3>
      <p class="lead">The Studio gets out of the way of the game.</p>
      <Switch label="Hide the Studio on Run" help="Run shrinks the Studio to a bar at the top of the screen with the bot's controls." bind:checked={values.collapseOnRun} onchange={(on) => onchange("studio.collapse_on_run", on)} />
      <div class="row">
        <span><b>The bar slides away after</b><small>Move a real mouse to the top edge to bring it back; the bot's own moves never do.</small></span>
        <select value={values.pillHideAfter} onchange={pickHide}>
          <option value="2">2 s</option><option value="3">3 s</option><option value="5">5 s</option><option value="never">never</option>
        </select>
      </div>
    {:else if section === "keys"}
      <h3>Keys</h3>
      <p class="lead">Ctrl+Alt+P pauses and Ctrl+Alt+Q stops any bot, anywhere. The key editor comes with a later version; for now keys live in <code>%APPDATA%\darbit\keymap.toml</code>.</p>
    {:else}
      <h3>About</h3>
      <p class="lead">darbit Studio runs your bots and edits them. Your settings stay on this PC in <code>%APPDATA%\darbit</code>; each bot keeps its own things in its folder.</p>
    {/if}
  </section>
</div>

<style>
  .studio-settings {
    display: grid;
    grid-template-columns: var(--width-tooltip) 1fr;
    gap: var(--space-l);
    align-items: start;
    max-width: calc(4 * var(--width-sheet));
    margin: 0 auto;
    width: 100%;
  }
  .sections {
    display: grid;
    gap: var(--space-xxs);
    padding: var(--space-m);
    border-radius: var(--radius-xl);
    background: var(--glass);
    border: 1px solid var(--line);
  }
  h2 {
    margin: var(--space-xs) var(--space-m) var(--space-m);
    font: 700 var(--size-subtitle) / var(--line-subtitle) var(--font-strong);
  }
  .sections button {
    display: flex;
    align-items: center;
    gap: var(--space-m);
    padding: var(--space-s) var(--space-m);
    border: 0;
    border-radius: var(--radius-m);
    background: none;
    color: var(--muted);
    font: 500 var(--size-body) / var(--line-body) var(--font);
    text-align: left;
    cursor: pointer;
    transition: background var(--duration-fast) var(--curve-easy-ease), color var(--duration-fast) var(--curve-easy-ease);
  }
  .sections button:hover {
    background: var(--raised);
    color: var(--text);
  }
  .sections button.on {
    background: var(--raised-hover);
    color: var(--text);
    box-shadow: inset 2px 0 0 var(--accent);
  }
  .form {
    display: grid;
    gap: var(--space-s);
    padding: var(--space-xl);
    border-radius: var(--radius-xl);
    background: var(--glass);
    border: 1px solid var(--line);
    animation: page-in var(--duration-normal) var(--curve-decelerate);
  }
  h3 {
    margin: 0;
    font: 700 var(--size-title3) / var(--line-title3) var(--font-strong);
  }
  .lead {
    margin: 0 0 var(--space-m);
    color: var(--muted);
  }
  .row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: var(--space-l);
    padding: var(--space-m) var(--space-l);
    border-radius: var(--radius-m);
    background: var(--raised);
  }
  .row > span:first-child {
    display: grid;
    gap: var(--space-xxs);
  }
  .row small {
    color: var(--muted);
    font-size: var(--size-caption);
  }
  .row select {
    font: inherit;
    color: var(--text);
    background: var(--raised-hover);
    border: 1px solid var(--line);
    border-radius: var(--radius-m);
    padding: var(--space-s) var(--space-m);
  }
  .tag {
    color: var(--muted);
    font-size: var(--size-caption);
  }
  @keyframes page-in {
    from {
      opacity: 0;
      transform: translateY(var(--space-s));
    }
  }
</style>
