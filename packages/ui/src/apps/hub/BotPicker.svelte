<!-- Picks the open bot: a dropdown at the top left, or a sidebar (the "Bot picker" Studio setting).
     Lists installed bots and added project folders with their status, and adds a folder. Decision 0013. -->
<script lang="ts">
  export interface Bot {
    path: string;
    name: string;
    version?: string;
    summary?: string;
    installed?: boolean;
    status: string;
    error?: string;
  }

  let {
    bots,
    bot,
    variant = "dropdown",
    onpick,
    onadd,
    onstudio,
    studioOpen = false,
  }: {
    bots: Bot[];
    bot: Bot | undefined;
    variant?: string;
    onpick: (bot: Bot) => void;
    onadd: (path: string) => void;
    onstudio: () => void;
    studioOpen?: boolean;
  } = $props();

  let open = $state(false);
  let folder = $state("");
  let root: HTMLElement | undefined = $state();

  function pick(next: Bot): void {
    open = false;
    onpick(next);
  }

  function add(event: Event): void {
    event.preventDefault();
    if (!folder.trim()) return;
    onadd(folder.trim());
    folder = "";
  }

  function initials(name: string): string {
    return name.slice(0, 2);
  }

  $effect(() => {
    if (!open) return;
    function away(event: PointerEvent): void {
      if (root && !root.contains(event.target as Node)) open = false;
    }
    function escape(event: KeyboardEvent): void {
      if (event.key === "Escape") open = false;
    }
    window.addEventListener("pointerdown", away);
    window.addEventListener("keydown", escape);
    return () => {
      window.removeEventListener("pointerdown", away);
      window.removeEventListener("keydown", escape);
    };
  });
</script>

{#snippet list()}
  {#each bots as each (each.path)}
    <button class="bot" class:on={each.path === bot?.path} onclick={() => pick(each)} title={each.path}>
      <span class="avatar">{initials(each.name)}</span>
      <span class="text"><b>{each.name}</b><small>{each.error ?? (each.summary || (each.installed ? `v${each.version ?? "?"}` : "project folder"))}</small></span>
      <span class="dot" data-status={each.status} aria-label={each.status}></span>
    </button>
  {/each}
  <form class="add" onsubmit={add}>
    <input bind:value={folder} placeholder="＋ Add a bot folder…" aria-label="Add a bot folder" />
  </form>
{/snippet}

{#if variant === "sidebar"}
  <nav class="sidebar" aria-label="Bots">
    <span class="label">Bots</span>
    {@render list()}
    <span class="grow"></span>
    <button class="studio" class:on={studioOpen} onclick={onstudio}><span aria-hidden="true">⚙</span>Studio</button>
  </nav>
{:else}
  <div class="dropdown" bind:this={root}>
    <button class="current" aria-expanded={open} onclick={() => (open = !open)}>
      <span class="avatar">{bot ? initials(bot.name) : "?"}</span>{bot?.name ?? "No bot"}<span class="caret" class:up={open} aria-hidden="true">▾</span>
    </button>
    <button class="gear" class:on={studioOpen} aria-label="Studio settings" title="Studio settings" onclick={onstudio}>⚙</button>
    {#if open}
      <div class="menu" role="menu">{@render list()}</div>
    {/if}
  </div>
{/if}

<style>
  .dropdown {
    position: relative;
    display: flex;
    align-items: center;
    gap: var(--space-s);
  }
  .current,
  .gear {
    display: inline-flex;
    align-items: center;
    gap: var(--space-m-nudge);
    height: var(--control-l);
    border: 1px solid var(--line);
    border-radius: var(--radius-pill);
    background: var(--glass);
    backdrop-filter: blur(var(--blur));
    color: var(--text);
    font: 650 var(--size-body) / 1 var(--font-strong);
    cursor: pointer;
    box-shadow: var(--shadow);
    transition: background var(--duration-fast) var(--curve-easy-ease);
  }
  .current {
    padding: 0 var(--space-m) 0 var(--space-xs);
  }
  .gear {
    width: var(--control-l);
    justify-content: center;
    padding: 0;
    color: var(--muted);
  }
  .current:hover,
  .gear:hover {
    background: var(--glass-strong);
  }
  .gear.on {
    background: var(--accent);
    color: var(--on-accent);
  }
  .caret {
    color: var(--muted);
    transition: rotate var(--duration-fast) var(--curve-easy-ease);
  }
  .caret.up {
    rotate: 180deg;
  }
  .menu {
    position: absolute;
    left: 0;
    top: calc(100% + var(--space-s));
    z-index: 20;
    width: var(--width-palette);
    display: grid;
    gap: var(--space-xxs);
    padding: var(--space-s);
    border-radius: var(--radius-xl);
    background: var(--glass-strong);
    border: 1px solid var(--line);
    box-shadow: var(--shadow);
    animation: drop var(--duration-normal) var(--curve-decelerate);
    transform-origin: top left;
  }
  @keyframes drop {
    from {
      opacity: 0;
      transform: translateY(calc(-1 * var(--space-s))) scale(0.98);
    }
  }
  .sidebar {
    display: flex;
    flex-direction: column;
    gap: var(--space-xxs);
    width: var(--width-tooltip);
    padding: var(--space-l) var(--space-m);
    border-right: 1px solid var(--line);
    background: color-mix(in oklab, var(--glass) 60%, transparent);
  }
  .label {
    padding: var(--space-s) var(--space-m);
    font: 700 var(--size-caption) / 1 var(--font-strong);
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: var(--faint);
  }
  .grow {
    flex: 1;
  }
  .bot,
  .studio {
    display: grid;
    grid-template-columns: auto 1fr auto;
    align-items: center;
    gap: var(--space-m);
    padding: var(--space-s) var(--space-m);
    border: 0;
    border-radius: var(--radius-l);
    background: none;
    color: var(--text);
    font: inherit;
    text-align: left;
    cursor: pointer;
    transition: background var(--duration-fast) var(--curve-easy-ease);
  }
  .studio {
    grid-template-columns: auto 1fr;
    color: var(--muted);
  }
  .bot:hover,
  .studio:hover {
    background: var(--raised);
  }
  .bot.on,
  .studio.on {
    background: var(--raised-hover);
    box-shadow: inset 2px 0 0 var(--accent);
  }
  .text {
    display: grid;
    min-width: 0;
  }
  .text b {
    font: 650 var(--size-body) / var(--line-body) var(--font-strong);
  }
  .text small {
    color: var(--muted);
    font-size: var(--size-caption);
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }
  .avatar {
    width: var(--control-m);
    height: var(--control-m);
    display: grid;
    place-items: center;
    border-radius: 50%;
    font: 800 var(--size-caption) / 1 var(--font-strong);
    color: var(--on-bot);
    background: var(--slot-bot);
    flex: none;
  }
  .dot {
    width: var(--space-s);
    height: var(--space-s);
    border-radius: 50%;
    background: var(--faint);
  }
  .dot[data-status="running"] {
    position: relative;
    background: var(--ok);
  }
  .dot[data-status="running"]::after {
    content: "";
    position: absolute;
    inset: 0;
    border-radius: 50%;
    background: var(--ok);
    animation: beat 2s ease-out infinite;
  }
  .dot[data-status="paused"] {
    background: var(--warn);
  }
  .dot[data-status="failed"],
  .dot[data-status="broken"] {
    background: var(--danger);
  }
  @keyframes beat {
    from {
      opacity: 0.5;
      transform: scale(1);
    }
    to {
      opacity: 0;
      transform: scale(2.6);
    }
  }
  .add input {
    width: 100%;
    box-sizing: border-box;
    margin-top: var(--space-xs);
    padding: var(--space-s) var(--space-m);
    border: 1px dashed var(--line);
    border-radius: var(--radius-l);
    background: none;
    color: var(--text);
    font: inherit;
    font-size: var(--size-caption);
  }
  .add input:focus {
    outline: none;
    border-color: var(--accent);
  }
</style>
