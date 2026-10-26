<!-- The tools dock at the bottom of the Studio: a pill of tool buttons, each with an icon in its colour and a
     name under it. Arrow keys move between them. A tool with `gap` starts a new group.
     <Dock tools={[{ label: "Capture", icon: "▣", tone: "kind-image", action: "capture.freeze" }]} /> -->
<script lang="ts">
  import { run } from "$lib/actions";
  import { keysFor } from "$lib/keymap";
  import { tip } from "$lib/tooltip";

  export interface Tool {
    label: string;
    icon: string;
    tone: string; // a colour token without "--", e.g. "kind-image"
    action?: string;
    onclick?: () => void;
    gap?: boolean;
  }

  let { tools, label = "Tools" }: { tools: Tool[]; label?: string } = $props();
  let buttons: HTMLButtonElement[] = $state([]);

  function press(tool: Tool): void {
    if (tool.onclick) tool.onclick();
    else if (tool.action) run(tool.action);
  }

  function onkeydown(event: KeyboardEvent, index: number): void {
    let next = index;
    if (event.key === "ArrowRight") next = (index + 1) % tools.length;
    else if (event.key === "ArrowLeft") next = (index - 1 + tools.length) % tools.length;
    else return;
    event.preventDefault();
    buttons[next]?.focus();
  }
</script>

<nav class="dock" aria-label={label}>
  {#each tools as tool, index (tool.label)}
    {#if tool.gap}<hr />{/if}
    <button
      bind:this={buttons[index]}
      style:--c="var(--{tool.tone})"
      tabindex={index === 0 ? 0 : -1}
      onclick={() => press(tool)}
      onkeydown={(event) => onkeydown(event, index)}
      use:tip={{ label: tool.label, keys: tool.action ? keysFor(tool.action) : undefined }}
    >
      <span class="icon" aria-hidden="true">{tool.icon}</span>{tool.label}
    </button>
  {/each}
</nav>

<style>
  .dock {
    display: flex;
    gap: var(--space-1);
    padding: 6px;
    border-radius: 22px;
    background: var(--glass);
    backdrop-filter: blur(var(--blur));
    border: 1px solid var(--line);
    box-shadow: var(--shadow);
    max-width: 100%;
    overflow-x: auto;
    scrollbar-width: none;
  }
  button {
    flex: none;
    width: 84px;
    display: grid;
    gap: var(--space-1);
    place-items: center;
    padding: var(--space-2) var(--space-1) 6px;
    border: 0;
    border-radius: 16px;
    background: none;
    color: var(--text);
    font: 600 var(--size-xs) / 1.2 var(--font-strong);
    cursor: pointer;
    transition:
      background var(--fast) var(--ease),
      transform var(--fast) var(--ease);
  }
  button:hover {
    background: var(--raised-hover);
    transform: translateY(-3px);
  }
  .icon {
    width: 40px;
    height: 40px;
    display: grid;
    place-items: center;
    border-radius: 12px;
    font-size: var(--size-l);
    color: var(--c);
    background: color-mix(in oklab, var(--c) 18%, transparent);
  }
  hr {
    width: 1px;
    margin: 10px var(--space-1);
    border: 0;
    background: var(--line);
  }
</style>
