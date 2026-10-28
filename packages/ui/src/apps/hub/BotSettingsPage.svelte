<!-- The bot's Settings page: change how it plays without code (decision 0013, round 5, layout S1). Sections from
     settings.toml on the left, one form on the right; a purple dot marks a value changed from its default, and a
     save bar slides up while there are unsaved changes. Saving writes config.toml (server/hub.py). -->
<script lang="ts">
  import type { Section, Setting } from "$lib/components/SettingsForm.svelte";

  let {
    sections,
    values,
    onsave,
  }: { sections: Section[]; values: Record<string, unknown>; onsave: (values: Record<string, unknown>) => Promise<void> } = $props();

  let chosen = $state(0);
  let query = $state("");
  let draft: Record<string, unknown> = $state({});
  let saving = $state(false);

  const current = $derived(sections[Math.min(chosen, sections.length - 1)]);
  const dirty = $derived(Object.keys(draft).filter((key) => JSON.stringify(draft[key]) !== JSON.stringify(values[key])));
  const found = $derived(query ? search(query) : []);

  function value(setting: Setting): unknown {
    if (setting.key in draft) return draft[setting.key];
    if (setting.key in values) return values[setting.key];
    return setting.default;
  }

  function set(setting: Setting, next: unknown): void {
    draft = { ...draft, [setting.key]: next };
  }

  function changed(setting: Setting): boolean {
    return JSON.stringify(value(setting)) !== JSON.stringify(setting.default);
  }

  function sectionChanged(section: Section): boolean {
    return section.settings.some(changed);
  }

  function search(text: string): Setting[] {
    const words = text.toLowerCase();
    const hits: Setting[] = [];
    for (const section of sections) {
      for (const setting of section.settings) {
        if ((setting.label + " " + setting.help + " " + setting.key).toLowerCase().includes(words)) hits.push(setting);
      }
    }
    return hits;
  }

  async function save(): Promise<void> {
    saving = true;
    try {
      await onsave({ ...values, ...draft });
      draft = {};
    } finally {
      saving = false;
    }
  }

  function numberFrom(event: Event, setting: Setting): void {
    const text = (event.currentTarget as HTMLInputElement).value;
    if (text === "") return;
    set(setting, setting.type === "int" ? Math.round(Number(text)) : Number(text));
  }

  function listFrom(event: Event, setting: Setting): void {
    const text = (event.currentTarget as HTMLInputElement).value;
    const items: string[] = [];
    for (const part of text.split(",")) if (part.trim()) items.push(part.trim());
    set(setting, items);
  }
</script>

{#snippet row(setting: Setting)}
  <div class="row">
    <span class="text">
      <b>{setting.label}{#if changed(setting)}<i class="changed" title="Changed from the default ({JSON.stringify(setting.default)})"></i>{/if}</b>
      {#if setting.help}<small>{setting.help}</small>{/if}
    </span>
    <span class="control">
      {#if setting.type === "bool"}
        <button class="switch" role="switch" aria-checked={value(setting) === true} aria-label={setting.label} onclick={() => set(setting, value(setting) !== true)}></button>
      {:else if setting.type === "int" || setting.type === "float"}
        <input type="number" value={value(setting)} min={setting.rules.min} max={setting.rules.max} step={setting.type === "int" ? 1 : "any"} oninput={(event) => numberFrom(event, setting)} aria-label={setting.label} />
      {:else if setting.type === "choice"}
        <select value={value(setting)} onchange={(event) => set(setting, event.currentTarget.value)} aria-label={setting.label}>
          {#each setting.rules.options ?? [] as option (option)}<option>{option}</option>{/each}
        </select>
      {:else if setting.type === "list"}
        <input value={Array.isArray(value(setting)) ? (value(setting) as string[]).join(", ") : ""} oninput={(event) => listFrom(event, setting)} aria-label={setting.label} placeholder="a, b, c" />
      {:else if setting.type === "region" || setting.type === "location"}
        <code>{Array.isArray(value(setting)) ? (value(setting) as number[]).join(", ") : "not set"}</code>
      {:else}
        <input value={String(value(setting) ?? "")} oninput={(event) => set(setting, event.currentTarget.value)} aria-label={setting.label} />
      {/if}
      {#if changed(setting)}
        <button class="reset" title="Back to the default" aria-label="Back to the default" onclick={() => set(setting, setting.default)}>↺</button>
      {/if}
    </span>
  </div>
{/snippet}

<div class="settings">
  <nav class="sections" aria-label="Setting sections">
    <input class="search" bind:value={query} placeholder="⌕ Search settings" aria-label="Search settings" />
    {#each sections as section, index (section.key)}
      <button class:on={!query && index === chosen} onclick={() => { chosen = index; query = ""; }}>
        {section.label || section.key}{#if sectionChanged(section)}<i class="changed"></i>{/if}
      </button>
    {/each}
  </nav>
  <section class="form">
    {#if query}
      <h2>Settings matching “{query}”</h2>
      {#each found as setting (setting.key)}{@render row(setting)}{:else}<p class="lead">Nothing matches.</p>{/each}
    {:else if current}
      <h2>{current.label || current.key}</h2>
      {#if current.help}<p class="lead">{current.help}</p>{/if}
      {#each current.settings as setting (setting.key)}{@render row(setting)}{/each}
    {/if}
  </section>
</div>

{#if dirty.length}
  <div class="savebar" role="status">
    <span>{dirty.length} change{dirty.length > 1 ? "s" : ""}</span>
    <button class="ghost" onclick={() => (draft = {})}>Undo</button>
    <button class="primary" disabled={saving} onclick={save}>{saving ? "Saving…" : "Save"}</button>
  </div>
{/if}

<style>
  .settings {
    display: grid;
    grid-template-columns: var(--width-tooltip) 1fr;
    gap: var(--space-l);
    align-items: start;
    max-width: calc(4 * var(--width-sheet));
    margin: 0 auto;
    width: 100%;
    padding-bottom: calc(2 * var(--control-l));
  }
  .sections {
    position: sticky;
    top: var(--space-l);
    display: grid;
    gap: var(--space-xxs);
    padding: var(--space-m);
    border-radius: var(--radius-xl);
    background: var(--glass);
    border: 1px solid var(--line);
  }
  .search {
    margin-bottom: var(--space-s);
    padding: var(--space-s) var(--space-m);
    border: 1px solid var(--line);
    border-radius: var(--radius-pill);
    background: var(--raised);
    color: var(--text);
    font: inherit;
    font-size: var(--size-caption);
  }
  .search:focus {
    outline: none;
    border-color: var(--accent);
  }
  .sections button {
    display: flex;
    align-items: center;
    justify-content: space-between;
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
  .changed {
    display: inline-block;
    width: var(--space-s);
    height: var(--space-s);
    margin-left: var(--space-s);
    border-radius: 50%;
    background: var(--accent-2);
    vertical-align: middle;
  }
  .form {
    display: grid;
    padding: var(--space-xl);
    border-radius: var(--radius-xl);
    background: var(--glass);
    border: 1px solid var(--line);
    animation: page-in var(--duration-normal) var(--curve-decelerate);
  }
  h2 {
    margin: 0 0 var(--space-xs);
    font: 700 var(--size-title3) / var(--line-title3) var(--font-strong);
  }
  .lead {
    margin: 0 0 var(--space-m);
    color: var(--muted);
  }
  .row {
    display: grid;
    grid-template-columns: 1fr auto;
    gap: var(--space-l);
    align-items: center;
    padding: var(--space-m) 0;
    border-bottom: 1px solid var(--line);
  }
  .row:last-child {
    border-bottom: 0;
  }
  .text {
    display: grid;
    gap: var(--space-xxs);
  }
  .text b {
    font: 600 var(--size-body) / var(--line-body) var(--font-strong);
  }
  .text small {
    color: var(--muted);
    font-size: var(--size-caption);
  }
  .control {
    display: flex;
    align-items: center;
    gap: var(--space-s);
  }
  .control input,
  .control select {
    min-width: calc(4 * var(--control-m));
    padding: var(--space-s) var(--space-m);
    border: 1px solid var(--line);
    border-radius: var(--radius-m);
    background: var(--raised);
    color: var(--text);
    font: inherit;
    font-size: var(--size-body);
  }
  .control input[type="number"] {
    min-width: 0;
    width: calc(3 * var(--control-m));
    text-align: right;
  }
  .control input:focus,
  .control select:focus {
    outline: none;
    border-color: var(--accent);
  }
  .switch {
    position: relative;
    width: calc(var(--control-m) + var(--space-m));
    height: var(--control-s);
    border: 0;
    border-radius: var(--radius-pill);
    background: var(--raised-hover);
    cursor: pointer;
    transition: background var(--duration-fast) var(--curve-easy-ease);
  }
  .switch::after {
    content: "";
    position: absolute;
    top: var(--space-xs);
    left: var(--space-xs);
    width: var(--space-l);
    height: var(--space-l);
    border-radius: 50%;
    background: var(--text);
    transition: translate var(--duration-normal) var(--curve-decelerate);
  }
  .switch[aria-checked="true"] {
    background: var(--accent);
  }
  .switch[aria-checked="true"]::after {
    translate: calc(var(--control-m) + var(--space-m) - var(--space-l) - 2 * var(--space-xs)) 0;
    background: var(--on-accent);
  }
  .reset {
    width: var(--control-s);
    height: var(--control-s);
    border: 0;
    border-radius: 50%;
    background: none;
    color: var(--muted);
    cursor: pointer;
  }
  .reset:hover {
    background: var(--raised);
    color: var(--text);
  }
  .savebar {
    position: fixed;
    left: 50%;
    bottom: var(--space-xl);
    translate: -50% 0;
    z-index: 20;
    display: flex;
    align-items: center;
    gap: var(--space-m);
    padding: var(--space-s) var(--space-s) var(--space-s) var(--space-l);
    border-radius: var(--radius-pill);
    background: var(--glass-strong);
    border: 1px solid var(--line);
    box-shadow: var(--shadow);
    font: 600 var(--size-body) / 1 var(--font-strong);
    animation: bar-up var(--duration-normal) var(--curve-decelerate);
  }
  .savebar button {
    height: var(--control-m);
    padding: 0 var(--space-l);
    border: 0;
    border-radius: var(--radius-pill);
    font: 650 var(--size-caption) / 1 var(--font-strong);
    cursor: pointer;
  }
  .savebar .ghost {
    background: var(--raised);
    color: var(--text);
  }
  .savebar .primary {
    background: var(--accent);
    color: var(--on-accent);
  }
  @keyframes page-in {
    from {
      opacity: 0;
      transform: translateY(var(--space-s));
    }
  }
  @keyframes bar-up {
    from {
      opacity: 0;
      transform: translateY(var(--space-l));
    }
  }
</style>
