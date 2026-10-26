<!-- darbit Studio: the bot switcher, the open bot's Overview, Library, Runs and Settings, run controls and the
     tools dock, all from the local server (server/hub.py). See docs/tasks/T20-hub.md. -->
<script lang="ts">
  import { register } from "$lib/actions";
  import { on, request } from "$lib/api";
  import Button from "$lib/components/Button.svelte";
  import Chip from "$lib/components/Chip.svelte";
  import CommandPalette from "$lib/components/CommandPalette.svelte";
  import Dock, { type Tool } from "$lib/components/Dock.svelte";
  import Field from "$lib/components/Field.svelte";
  import IconButton from "$lib/components/IconButton.svelte";
  import Pill from "$lib/components/Pill.svelte";
  import ScoreBadge from "$lib/components/ScoreBadge.svelte";
  import Segmented from "$lib/components/Segmented.svelte";
  import SettingsForm, { type Section } from "$lib/components/SettingsForm.svelte";
  import Sheet from "$lib/components/Sheet.svelte";
  import Switch from "$lib/components/Switch.svelte";
  import Toast from "$lib/components/Toast.svelte";
  import { toast } from "$lib/toasts.svelte";
  import { chooseTheme, currentTheme, THEMES, type ThemeName } from "$lib/theme";
  import TileView, { type TileData } from "./TileView.svelte";

  interface Bot {
    path: string;
    name: string;
    version?: string;
    summary?: string;
    installed?: boolean;
    status: string;
    error?: string;
  }

  interface Picture {
    name: string;
    thumbnail: string | null;
    score: number | null;
  }

  const SECTIONS = [
    { value: "overview", label: "Overview", icon: "◉" },
    { value: "library", label: "Library", icon: "▣" },
    { value: "runs", label: "Runs", icon: "≡" },
    { value: "settings", label: "Settings", icon: "⚙" },
  ];
  const THEME_LABELS: Record<ThemeName, string> = {
    "glass-dark": "Glass dark",
    "glass-light": "Glass light",
    midnight: "Midnight",
    "high-contrast": "High contrast",
  };

  let { connected = false }: { connected?: boolean } = $props();

  let section = $state("overview");
  let bots: Bot[] = $state([]);
  let bot: Bot | undefined = $state();
  let tiles: TileData[] = $state([]);
  let pictures: Picture[] = $state([]);
  let days: string[] = $state([]);
  let day = $state("");
  let dayTiles: TileData[] = $state([]);
  let form: { sections: Section[]; values: Record<string, unknown>; error: string | null } = $state({ sections: [], values: {}, error: null });
  let botsOpen = $state(false);
  let appOpen = $state(false);
  let palette = $state(false);
  let sources = $state(false);
  let theme: ThemeName = $state(currentTheme());
  let folderToAdd = $state("");
  let problem = $state("");
  let collapseOnRun = $state(true); // the Studio hides behind the run pill while a bot runs (issue 130)
  let ready = $state(false); // the bots list arrived
  let loading = $state(false); // no "nothing here" while a section is still on its way

  const status = $derived(bot?.status ?? "stopped");

  const TOOLS: Tool[] = [
    { label: "Capture", icon: "▣", tone: "kind-image", onclick: () => openTool("capture") },
    { label: "Guide", icon: "☰", tone: "warn", onclick: () => openTool("guide") },
    { label: "Check", icon: "✓", tone: "info", onclick: () => openTool("check") },
  ];

  function failed(error: Error): void {
    toast(error.message);
  }

  async function loadBots(): Promise<void> {
    bots = await request<Bot[]>("projects.list");
    const kept = bots.find((each) => each.path === bot?.path);
    if (kept) bot = kept;
    else if (bots.length) await openBot(bots[0]);
  }

  async function openBot(next: Bot): Promise<void> {
    bot = next;
    botsOpen = false;
    tiles = [];
    pictures = [];
    days = [];
    dayTiles = [];
    await loadSection();
  }

  async function loadSection(): Promise<void> {
    if (!bot) return;
    const path = bot.path;
    loading = true;
    try {
      await loadPart(path);
    } finally {
      loading = false;
    }
  }

  async function loadPart(path: string): Promise<void> {
    if (section === "overview") {
      const overview = await request("dashboard.tiles", { path });
      tiles = overview.tiles;
      if (bot?.path === path) bot = { ...bot, ...overview.project };
    } else if (section === "library") {
      pictures = await request<Picture[]>("library.list", { path });
    } else if (section === "runs") {
      days = await request<string[]>("reports.days", { path });
      if (!days.includes(day)) day = days[0] ?? "";
      await loadDay();
    } else if (section === "settings") {
      form = await request("project.settings", { path });
    }
  }

  async function loadDay(): Promise<void> {
    if (!bot || !day) {
      dayTiles = [];
      return;
    }
    const overview = await request("dashboard.tiles", { path: bot.path, day });
    dayTiles = overview.tiles.filter((tile: TileData) => tile.kind !== "now");
  }

  async function control(type: "project.run" | "project.pause" | "project.stop"): Promise<void> {
    if (!bot) return;
    const path = bot.path;
    const reply = await request(type, { path }).catch(failed);
    if (!reply) return;
    bot = { ...bot, status: reply.status };
    if (type === "project.run" && collapseOnRun) {
      request("studio.collapse", { path }).catch(() => {
        // no desktop window (opened in a browser): the Studio stays as it is
      });
    }
  }

  function pickCollapse(checked: boolean): void {
    request("settings.set", { key: "studio.collapse_on_run", value: checked }).catch(failed);
  }

  async function saveSettings(values: Record<string, unknown>): Promise<void> {
    if (!bot) return;
    await request("project.settings.save", { path: bot.path, values })
      .then(() => toast("Settings saved. The bot reads them when it starts."))
      .catch(failed);
  }

  async function openTool(tool: string): Promise<void> {
    if (!bot) return;
    await request("tools.open", { path: bot.path, tool })
      .then(() => toast(`Opening ${tool} for ${bot?.name}`))
      .catch(failed);
  }

  async function addFolder(): Promise<void> {
    const added = await request<Bot>("project.add", { path: folderToAdd.trim() }).catch(failed);
    if (!added) return;
    folderToAdd = "";
    await loadBots();
    await openBot(added);
  }

  function pickTheme(event: Event): void {
    theme = (event.target as HTMLSelectElement).value as ThemeName;
    chooseTheme(theme);
  }

  $effect(() => {
    if (!connected) return;
    request("settings.get", { key: "studio.collapse_on_run" }).then((value) => (collapseOnRun = value !== false));
    loadBots()
      .catch((error: Error) => (problem = error.message))
      .finally(() => (ready = true));
    const stopStatus = on("project.status", (data) => {
      bots = bots.map((each) => (each.path === data.path ? { ...each, status: data.status } : each));
      const shown = bot;
      if (shown && shown.path === data.path) {
        bot = { ...shown, status: data.status };
        if (data.status === "failed") toast(`${shown.name} stopped with an error`, "bot", shown.name);
      }
    });
    const stopChanged = on("project.changed", (data) => {
      if (bot?.path === data.path && section === "overview") loadSection().catch(failed);
    });
    return () => {
      stopStatus();
      stopChanged();
    };
  });

  $effect(() => {
    section; // reload when the section changes
    if (connected && bot) loadSection().catch(failed);
  });

  register({ name: "palette.open", label: "Commands", run: () => (palette = true) });
  register({ name: "hub.section.next", label: "Next section", run: () => (section = SECTIONS[(SECTIONS.findIndex((each) => each.value === section) + 1) % SECTIONS.length].value) });
  register({ name: "studio.overview", label: "Go to Overview", run: () => (section = "overview") });
  register({ name: "studio.library", label: "Go to Library", run: () => (section = "library") });
  register({ name: "studio.runs", label: "Go to Runs", run: () => (section = "runs") });
  register({ name: "studio.settings", label: "Go to Settings", run: () => (section = "settings") });
  register({ name: "hub.run.toggle", label: "Run or stop the bot", run: () => control(status === "stopped" || status === "failed" ? "project.run" : "project.stop") });
  register({ name: "run.pause", label: "Pause the bot", run: () => control("project.pause") });
</script>

<div class="studio">
  <header class="top">
    <div class="anchor">
      <Pill label="Bot">
        <button class="switcher" aria-expanded={botsOpen} onclick={() => (botsOpen = !botsOpen)}>
          <span class="avatar">{bot ? bot.name.slice(0, 2) : "?"}</span>{bot?.name ?? "No bot"}<span class="caret" aria-hidden="true">▾</span>
        </button>
      </Pill>
      <Sheet title="Your bots" bind:open={botsOpen} side="left" width={620}>
        <div class="bots">
          {#each bots as each (each.path)}
            <button class="bot" class:on={each.path === bot?.path} onclick={() => openBot(each)}>
              <b>{each.name} {#if each.version}<em>v{each.version}</em>{/if}</b>
              <span>{each.error ?? (each.summary || each.path)}</span>
              <Chip text={each.status} tone={each.status === "running" ? "ok" : each.status === "failed" || each.status === "broken" ? "danger" : "neutral"} />
            </button>
          {/each}
        </div>
        <form class="add" onsubmit={(event) => { event.preventDefault(); addFolder(); }}>
          <Field label="Add a project folder" help="A folder with a darbit.toml, such as a bot you're writing.">
            <input bind:value={folderToAdd} placeholder="C:\Users\me\Projects\my-bot" />
          </Field>
          <Button label="Add" icon="＋" variant="primary" size="s" disabled={!folderToAdd.trim()} onclick={addFolder} />
        </form>
      </Sheet>
    </div>
    <Segmented items={SECTIONS} bind:value={section} label="Studio sections" variant="nav" />
    <Pill label="Run controls">
      <span class="running" class:live={status === "running"} class:held={status === "paused"}>
        <span class="dot"></span><b>{status[0].toUpperCase() + status.slice(1)}</b>
      </span>
      {#if status === "running" || status === "paused"}
        <IconButton label={status === "paused" ? "Resume" : "Pause"} icon={status === "paused" ? "▶" : "❚❚"} action="run.pause" />
        <IconButton label="Stop" icon="■" onclick={() => control("project.stop")} />
      {:else}
        <IconButton label="Run" icon="▶" action="hub.run.toggle" disabled={!bot || status === "broken"} />
      {/if}
    </Pill>
    <div class="anchor">
      <Pill label="Studio">
        <IconButton label="Where each tile comes from" icon="‹/›" bind:pressed={sources} />
        <IconButton label="Studio settings" icon="⚙" onclick={() => (appOpen = !appOpen)} />
      </Pill>
      <Sheet title="Studio" bind:open={appOpen} side="right" width={360}>
        <Field label="Theme">
          <select value={theme} onchange={pickTheme}>
            {#each THEMES as name (name)}<option value={name}>{THEME_LABELS[name]}</option>{/each}
          </select>
        </Field>
        <Switch label="Hide while a bot runs" help="Run shrinks the Studio to a bar at the top of the screen. It slides away; move the mouse to the top edge to bring it back." bind:checked={collapseOnRun} onchange={pickCollapse} />
      </Sheet>
    </div>
  </header>

  <main>
    {#if !connected}
      <p class="empty">darbit Studio needs darbit's local server. Start it with <code>darbit app</code>.</p>
    {:else if problem}
      <p class="empty">{problem}</p>
    {:else if !ready}
      <span></span>
    {:else if !bot}
      <p class="empty">No bots yet. Install one with <code>darbit install &lt;link&gt;</code>, or add a project folder from the bot menu.</p>
    {:else if section === "overview"}
      <div class="bento">
        {#each tiles as tile (tile.kind)}
          <TileView {tile} showSource={sources} />
        {/each}
      </div>
    {:else if section === "library"}
      {#if pictures.length}
        <div class="library">
          {#each pictures as picture (picture.name)}
            <figure>
              {#if picture.thumbnail}<img src={picture.thumbnail} alt="" />{:else}<span class="nothumb">?</span>{/if}
              <figcaption>
                <span>{picture.name}</span>
                {#if picture.score !== null}<ScoreBadge score={picture.score} />{/if}
              </figcaption>
            </figure>
          {/each}
        </div>
      {:else if !loading}
        <p class="empty">No pictures yet. Take them with the Guide in the dock.</p>
      {/if}
    {:else if section === "runs"}
      {#if days.length}
        <div class="runs">
          <Field label="Day">
            <select bind:value={day} onchange={() => loadDay().catch(failed)}>
              {#each days as each (each)}<option value={each}>{each}</option>{/each}
            </select>
          </Field>
          <div class="bento">
            {#each dayTiles as tile (tile.kind)}
              <TileView {tile} showSource={sources} />
            {/each}
          </div>
        </div>
      {:else if !loading}
        <p class="empty">No runs yet.</p>
      {/if}
    {:else if section === "settings"}
      {#if form.error}
        <p class="empty bad">{form.error}</p>
      {:else if form.sections.length}
        <SettingsForm sections={form.sections} values={form.values} onsave={saveSettings} showSource={sources} />
      {:else if !loading}
        <p class="empty">This bot has no settings.toml.</p>
      {/if}
    {/if}
  </main>

  <div class="dock"><Dock tools={TOOLS} /></div>
  <CommandPalette bind:open={palette} />
  <Toast />
</div>

<style>
  .studio {
    position: relative;
    min-height: 100vh;
    display: grid;
    grid-template-rows: auto 1fr;
    gap: var(--space-l);
    padding: var(--space-xxl) var(--space-xxl) calc(3 * var(--control-l));
    font-size: var(--size-content);
    background: var(--bg);
    color: var(--text);
    box-sizing: border-box;
  }
  .top {
    display: flex;
    align-items: center;
    gap: var(--space-m);
    position: relative;
    z-index: 5;
  }
  .top > :global(.segmented) {
    margin: 0 auto;
  }
  .anchor {
    position: relative;
  }
  .switcher {
    display: inline-flex;
    align-items: center;
    gap: var(--space-m-nudge);
    padding: var(--space-xs) var(--space-m) var(--space-xs) var(--space-xs);
    border: 0;
    border-radius: var(--radius-pill);
    background: none;
    color: var(--text);
    font: 650 var(--size-body) / 1 var(--font-strong);
    cursor: pointer;
  }
  .switcher:hover {
    background: var(--raised-hover);
  }
  .avatar {
    width: var(--control-m);
    height: var(--control-m);
    display: grid;
    place-items: center;
    border-radius: 50%;
    font-size: var(--size-caption);
    font-weight: 800;
    color: var(--on-bot);
    background: var(--slot-bot);
  }
  .caret {
    color: var(--muted);
  }
  .running {
    display: inline-flex;
    align-items: center;
    gap: var(--space-s-nudge);
    padding: 0 var(--space-s-nudge) 0 var(--space-m);
    font-size: var(--size-caption);
    color: var(--muted);
    white-space: nowrap;
  }
  .running b {
    color: var(--text);
  }
  .dot {
    width: var(--space-s);
    height: var(--space-s);
    border-radius: 50%;
    background: var(--faint);
  }
  .live .dot {
    background: var(--ok);
  }
  .held .dot {
    background: var(--warn);
  }
  .bots {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: var(--space-m);
  }
  .bot {
    display: grid;
    gap: var(--space-s);
    justify-items: start;
    padding: var(--space-l);
    border: 0;
    border-radius: var(--radius-xl);
    background: var(--raised);
    color: var(--text);
    font: inherit;
    text-align: left;
    cursor: pointer;
  }
  .bot:hover {
    background: var(--raised-hover);
  }
  .bot.on {
    box-shadow: var(--glow);
  }
  .bot em {
    font-style: normal;
    font-weight: 400;
    color: var(--muted);
  }
  .bot span {
    color: var(--muted);
    font-size: var(--size-caption);
    word-break: break-all;
  }
  .add {
    display: flex;
    align-items: end;
    gap: var(--space-m);
    margin-top: var(--space-xl);
  }
  .add :global(.field) {
    flex: 1;
  }
  .bento {
    display: grid;
    grid-template-columns: repeat(12, 1fr);
    grid-auto-flow: dense; /* a narrow tile fills the gap beside a wide one */
    gap: var(--space-l);
    align-content: start;
  }
  .library {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(calc(5 * var(--control-l)), 1fr));
    gap: var(--space-l);
  }
  figure {
    margin: 0;
    display: grid;
    gap: var(--space-s);
    padding: var(--space-m);
    border-radius: var(--radius-l);
    background: var(--raised);
  }
  figure img,
  .nothumb {
    width: 100%;
    height: calc(2 * var(--control-l));
    object-fit: contain;
    display: grid;
    place-items: center;
    color: var(--faint);
  }
  figcaption {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: var(--space-s);
    font-size: var(--size-caption);
    word-break: break-all;
  }
  .runs {
    display: grid;
    gap: var(--space-l);
    align-content: start;
  }
  .runs > :global(.field) {
    max-width: var(--width-inspector);
  }
  .empty {
    color: var(--muted);
    margin: var(--space-xxl) auto;
    text-align: center;
  }
  .bad {
    color: var(--danger);
  }
  .dock {
    position: fixed;
    left: 50%;
    bottom: var(--space-xxl);
    translate: -50% 0;
    z-index: 5;
  }
</style>
