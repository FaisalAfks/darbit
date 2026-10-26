<!-- ctrl+k: every action in this window by name, with its keys. Type to filter (letters in order, so "cpt"
     finds "Capture"), arrows move, Enter runs, Esc closes. See docs/tasks/T03-components.md step 7. -->
<script lang="ts">
  import { available, run, type Action } from "$lib/actions";
  import { keysFor } from "$lib/keymap";
  import Keycap from "./Keycap.svelte";

  let { open = $bindable(false) }: { open?: boolean } = $props();
  let query = $state("");
  let chosen = $state(0);
  let input: HTMLInputElement | undefined = $state();

  /** How well `label` matches `typed`: its letters in order, earlier and closer together is better; -1 if not. */
  function score(label: string, typed: string): number {
    const text = label.toLowerCase();
    let at = 0;
    let total = 0;
    for (const letter of typed.toLowerCase()) {
      const found = text.indexOf(letter, at);
      if (found < 0) return -1;
      total += found - at;
      at = found + 1;
    }
    return total;
  }

  function matching(typed: string): Action[] {
    const scored: { action: Action; score: number }[] = [];
    for (const action of available()) {
      const value = score(action.label, typed);
      if (value >= 0) scored.push({ action, score: value });
    }
    scored.sort((a, b) => a.score - b.score);
    return scored.map((entry) => entry.action);
  }

  const found = $derived(matching(query));

  $effect(() => {
    if (open) {
      query = "";
      chosen = 0;
      input?.focus();
    }
  });

  function choose(action: Action | undefined): void {
    if (!action) return;
    open = false;
    run(action.name);
  }

  function onkeydown(event: KeyboardEvent): void {
    if (event.key === "ArrowDown") chosen = Math.min(chosen + 1, found.length - 1);
    else if (event.key === "ArrowUp") chosen = Math.max(chosen - 1, 0);
    else if (event.key === "Enter") choose(found[chosen]);
    else if (event.key === "Escape") open = false;
    else return;
    event.preventDefault();
  }
</script>

{#if open}
  <div class="backdrop" role="presentation" onclick={() => (open = false)}></div>
  <div class="palette appear" role="dialog" aria-label="Commands">
    <input
      bind:this={input}
      bind:value={query}
      oninput={() => (chosen = 0)}
      {onkeydown}
      placeholder="Type a command"
      role="combobox"
      aria-expanded="true"
      aria-controls="palette-list"
      aria-activedescendant={found[chosen] ? `palette-${found[chosen].name}` : undefined}
    />
    <ul id="palette-list" role="listbox" aria-label="Commands">
      {#each found as action, index (action.name)}
        {@const keys = keysFor(action.name)}
        <li
          id="palette-{action.name}"
          role="option"
          aria-selected={index === chosen}
          onclick={() => choose(action)}
          onkeydown={() => {}}
          onpointerenter={() => (chosen = index)}
        >
          <span>{action.label}</span>{#if keys}<Keycap {keys} />{/if}
        </li>
      {:else}
        <li class="none">Nothing matches "{query}"</li>
      {/each}
    </ul>
  </div>
{/if}

<style>
  .backdrop {
    position: fixed;
    inset: 0;
    z-index: 49;
    background: color-mix(in oklab, var(--bg) 40%, transparent);
  }
  .palette {
    position: fixed;
    z-index: 50;
    top: 16%;
    left: 50%;
    translate: -50% 0;
    width: min(var(--width-palette), calc(100vw - 2 * var(--space-l)));
    padding: var(--space-s);
    background: var(--glass-strong);
    backdrop-filter: blur(var(--blur));
    border: 1px solid var(--line);
    border-radius: var(--radius-xl);
    box-shadow: var(--shadow);
  }
  input {
    width: 100%;
    padding: var(--space-m) var(--space-l);
    border: 0;
    border-radius: var(--radius-m);
    background: var(--raised);
    color: var(--text);
    font: var(--size-subtitle) / 1.3 var(--font);
  }
  ul {
    list-style: none;
    margin: var(--space-s) 0 0;
    padding: 0;
    max-height: calc(8 * var(--control-l));
    overflow: auto;
  }
  li {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: var(--space-m);
    padding: var(--space-m-nudge) var(--space-l);
    border-radius: var(--radius-m);
    font-size: var(--size-body);
    cursor: pointer;
  }
  [aria-selected="true"] {
    background: var(--raised-hover);
  }
  .none {
    color: var(--muted);
    cursor: default;
  }
</style>
