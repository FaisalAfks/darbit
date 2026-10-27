<!-- Library › Actions: the bot's recorded and written actions, Record (with Edit on), and the action editor.
     Decision 0013, round 8. -->
<script lang="ts">
  import { request } from "$lib/api";
  import { toast } from "$lib/toasts.svelte";
  import ActionEditor from "./ActionEditor.svelte";

  interface Entry {
    name: string;
    steps: number;
    sections: number;
    used_by: string[];
    error?: string;
  }

  let { path, editing, thumbnails, opened = $bindable("") }: { path: string; editing: boolean; thumbnails: Record<string, string>; opened?: string } = $props();

  let actions: Entry[] = $state([]);
  let loaded = $state(false);
  let naming = $state(false);
  let newName = $state("");

  async function load(): Promise<void> {
    actions = await request<Entry[]>("actions.list", { path });
    loaded = true;
  }

  async function record(): Promise<void> {
    const name = newName.trim();
    if (!/^[A-Za-z_][A-Za-z0-9_]*$/.test(name)) {
      toast("Name it with letters, digits and _, like dodge or speed_raid_fight");
      return;
    }
    naming = false;
    await request("record.start", { path, name }).catch((error: Error) => {
      toast(error.message.includes("unknown request") ? "Recording starts from the desktop Studio (darbit app)" : error.message);
    });
  }

  $effect(() => {
    path;
    if (!opened) load().catch((error: Error) => toast(error.message));
  });
</script>

{#if opened}
  {#key opened}<ActionEditor {path} name={opened} {thumbnails} onback={() => (opened = "")} />{/key}
{:else}
  <div class="actions">
    <div class="bar">
      <span class="muted">Actions are steps the bot plays: recorded, or written as Python in <code>actions/</code>.</span>
      <span class="grow"></span>
      {#if editing}
        {#if naming}
          <form class="name" onsubmit={(event) => { event.preventDefault(); record(); }}>
            <input bind:value={newName} placeholder="its name, e.g. dodge" spellcheck="false" aria-label="The new action's name" />
            <button class="rec" type="submit">● Start recording</button>
            <button class="tool" type="button" onclick={() => (naming = false)}>Cancel</button>
          </form>
        {:else}
          <button class="rec" onclick={() => (naming = true)}>● Record</button>
        {/if}
      {:else}
        <span class="muted">✎ Edit to record or change actions</span>
      {/if}
    </div>
    {#if loaded && !actions.length}
      <p class="empty">No actions yet. Turn on Edit and press ● Record: play, and every key and click becomes a step.</p>
    {/if}
    <div class="grid">
      {#each actions as entry (entry.name)}
        <button class="card" onclick={() => (opened = entry.name)} disabled={!!entry.error}>
          <span class="icon">●</span>
          <span class="text">
            <b>{entry.name}</b>
            <small>{entry.error ?? `${entry.steps} steps · ${entry.sections} section${entry.sections === 1 ? "" : "s"}`}</small>
            {#if entry.used_by.length}<small class="used">used by {entry.used_by.join(", ")}</small>{/if}
          </span>
          <span class="go">›</span>
        </button>
      {/each}
    </div>
  </div>
{/if}

<style>
  .actions {
    display: grid;
    gap: var(--space-m);
  }
  .bar {
    display: flex;
    align-items: center;
    gap: var(--space-m);
    flex-wrap: wrap;
  }
  .grow {
    flex: 1;
  }
  .muted {
    color: var(--muted);
    font-size: var(--size-caption);
  }
  .name {
    display: flex;
    gap: var(--space-s);
  }
  .name input {
    padding: var(--space-s) var(--space-m);
    border: 1px solid var(--line);
    border-radius: var(--radius-pill);
    background: var(--raised);
    color: var(--text);
    font: 600 var(--size-body) / 1 var(--mono);
  }
  .rec {
    height: var(--control-m);
    padding: 0 var(--space-l);
    border: 0;
    border-radius: var(--radius-pill);
    background: color-mix(in oklab, var(--danger) 20%, transparent);
    color: var(--danger);
    font: 700 var(--size-caption) / 1 var(--font-strong);
    cursor: pointer;
  }
  .tool {
    height: var(--control-m);
    padding: 0 var(--space-m);
    border: 0;
    border-radius: var(--radius-pill);
    background: var(--raised);
    color: var(--text);
    font: 600 var(--size-caption) / 1 var(--font-strong);
    cursor: pointer;
  }
  .grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(calc(7 * var(--control-l)), 1fr));
    gap: var(--space-m);
  }
  .card {
    display: grid;
    grid-template-columns: auto 1fr auto;
    gap: var(--space-m);
    align-items: center;
    padding: var(--space-m) var(--space-l);
    border: 1px solid var(--line);
    border-radius: var(--radius-l);
    background: var(--glass);
    color: var(--text);
    font: inherit;
    text-align: left;
    cursor: pointer;
    transition: transform var(--duration-normal) var(--curve-decelerate), border-color var(--duration-fast) var(--curve-easy-ease);
  }
  .card:hover:not(:disabled) {
    transform: translateY(calc(-1 * var(--space-xxs)));
    border-color: color-mix(in oklab, var(--danger) 40%, transparent);
  }
  .card:disabled {
    opacity: 0.6;
    cursor: default;
  }
  .icon {
    width: var(--control-m);
    height: var(--control-m);
    display: grid;
    place-items: center;
    border-radius: var(--radius-m);
    background: color-mix(in oklab, var(--danger) 16%, transparent);
    color: var(--danger);
  }
  .text {
    display: grid;
  }
  .text b {
    font: 700 var(--size-body) / 1.3 var(--mono);
  }
  .text small {
    color: var(--muted);
    font-size: var(--size-caption);
  }
  .used {
    color: var(--slot-bot) !important;
  }
  .go {
    color: var(--faint);
    font-size: var(--size-title3);
  }
  .empty {
    color: var(--muted);
    margin: var(--space-xxl) auto;
    text-align: center;
  }
</style>
