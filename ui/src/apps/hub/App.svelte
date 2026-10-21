<!-- The hub: bots, the open bot (live, settings, setup), library, runs, settings. See docs/tasks/T20-hub.md. -->
<script lang="ts">
  import { register } from "$lib/actions";
  import CommandPalette from "$lib/components/CommandPalette.svelte";
  import ThemeSwitch from "$lib/components/ThemeSwitch.svelte";

  const SECTIONS = ["Bots", "Bot", "Library", "Runs", "Settings"] as const;
  let section: (typeof SECTIONS)[number] = $state("Bots");
  let palette = $state(false);

  register({ name: "hub.section.next", label: "Next section", run: () => (section = SECTIONS[(SECTIONS.indexOf(section) + 1) % SECTIONS.length]) });
  register({ name: "palette.open", label: "Commands", run: () => (palette = true) });
  // TODO(T20): each section's page; hub.run.toggle; view.compact (the mini pill)
</script>

<div class="hub">
  <nav class="rail" aria-label="Sections">
    <span class="logo">d</span>
    {#each SECTIONS as name}
      <button class:on={section === name} onclick={() => (section = name)}>{name}</button>
    {/each}
    <span class="grow"></span>
    <ThemeSwitch />
  </nav>
  <main>
    <h1>{section}</h1>
    <p class="todo">TODO(T20): the {section} page.</p>
  </main>
</div>
<CommandPalette bind:open={palette} />

<style>
  .hub { display: grid; grid-template-columns: 88px 1fr; height: 100vh; background: var(--bg); }
  .rail {
    display: flex; flex-direction: column; gap: var(--space-1); padding: var(--space-3) var(--space-2);
    background: var(--glass); border-right: 1px solid var(--line);
  }
  .logo {
    width: 32px; height: 32px; margin: 0 auto var(--space-3); display: grid; place-items: center; border-radius: 10px;
    background: linear-gradient(135deg, var(--accent), var(--accent-2)); color: var(--on-accent); font-weight: 800;
  }
  .rail button {
    border: 0; background: none; color: var(--muted); padding: 6px; border-radius: var(--radius-m);
    font: 600 var(--size-xs) var(--font-strong); cursor: pointer; transition: background var(--fast) var(--ease);
  }
  .rail button:hover { background: var(--raised-hover); color: var(--text); }
  .rail button.on { background: var(--raised); color: var(--accent); box-shadow: var(--glow); }
  .grow { flex: 1; }
  main { padding: var(--space-5); overflow: auto; }
  h1 { font: 600 var(--size-xl) var(--font-strong); margin: 0 0 var(--space-3); }
  .todo { color: var(--muted); }
</style>
