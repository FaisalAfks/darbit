<!-- darbit Studio: the bot picker (dropdown or sidebar), the centred page bar, the bot's controls, and the open
     page, all from the local server (server/hub.py). See decision 0013 and docs/ui/redesign/. -->
<script lang="ts">
  import { register } from "$lib/actions";
  import { on, request } from "$lib/api";
  import CommandPalette from "$lib/components/CommandPalette.svelte";
  import Segmented from "$lib/components/Segmented.svelte";
  import type { Section } from "$lib/components/SettingsForm.svelte";
  import Toast from "$lib/components/Toast.svelte";
  import { toast } from "$lib/toasts.svelte";
  import { currentTheme } from "$lib/theme";
  import BotPicker, { type Bot } from "./BotPicker.svelte";
  import BotSettingsPage from "./BotSettingsPage.svelte";
  import LibraryPage from "./LibraryPage.svelte";
  import OverviewPage from "./OverviewPage.svelte";
  import ResultsPage from "./ResultsPage.svelte";
  import StudioSettings, { type StudioValues } from "./StudioSettings.svelte";
  import type { TileData } from "./TileView.svelte";

  const PAGES = [
    { value: "overview", label: "Overview" },
    { value: "results", label: "Results" },
    { value: "library", label: "Library" },
    { value: "settings", label: "Settings" },
  ];

  let { connected = false }: { connected?: boolean } = $props();

  let page = $state(firstPage()); // a bot page, or "studio" for the Studio's own settings
  let bots: Bot[] = $state([]);
  let bot: Bot | undefined = $state();
  let tiles: TileData[] = $state([]);
  let form: { sections: Section[]; values: Record<string, unknown>; error: string | null } = $state({ sections: [], values: {}, error: null });
  let palette = $state(false);
  let editing = $state(false); // Edit unlocks adding and changing the bot's things
  let problem = $state("");
  let ready = $state(false); // the bots list arrived
  let loading = $state(false); // no "nothing here" while a page is still on its way
  let lastBotPage = "overview";
  let studio: StudioValues = $state({
    theme: currentTheme(),
    picker: "dropdown",
    effects: true,
    closing: "tray",
    collapseOnRun: true,
    pillHideAfter: "3",
  });

  const status = $derived(bot?.status ?? "stopped");
  const live = $derived(status === "running" || status === "paused");
  const botPage = $derived(page === "studio" ? "" : page);

  function firstPage(): string {
    const asked = new URLSearchParams(location.search).get("page") ?? "";
    if (asked === "studio" || PAGES.some((each) => each.value === asked)) return asked;
    return "overview";
  }

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
    tiles = [];
    if (page === "studio") page = lastBotPage;
    await loadPage();
  }

  async function loadPage(): Promise<void> {
    if (!bot || page === "studio") return;
    const path = bot.path;
    loading = true;
    try {
      await loadPart(path);
    } finally {
      loading = false;
    }
  }

  async function loadPart(path: string): Promise<void> {
    if (page === "overview") {
      const overview = await request("dashboard.tiles", { path });
      tiles = overview.tiles;
      if (bot?.path === path) bot = { ...bot, ...overview.project };
    } else if (page === "settings") {
      form = await request("project.settings", { path });
    }
  }

  async function control(type: "project.run" | "project.pause" | "project.stop"): Promise<void> {
    if (!bot) return;
    const path = bot.path;
    const reply = await request(type, { path }).catch(failed);
    if (!reply) return;
    bot = { ...bot, status: reply.status };
    if (type === "project.run" && studio.collapseOnRun) {
      request("studio.collapse", { path }).catch(() => {
        // no desktop window (opened in a browser): the Studio stays as it is
      });
    }
  }

  async function saveSettings(values: Record<string, unknown>): Promise<void> {
    if (!bot) return;
    const path = bot.path;
    await request("project.settings.save", { path, values })
      .then(() => toast("Settings saved. The bot reads them when it starts."))
      .catch(failed);
    form = await request("project.settings", { path });
  }

  async function openTool(tool: string): Promise<void> {
    if (!bot) return;
    await request("tools.open", { path: bot.path, tool })
      .then(() => toast(`Opening ${tool} for ${bot?.name}`))
      .catch(failed);
  }

  async function addFolder(path: string): Promise<void> {
    const added = await request<Bot>("project.add", { path }).catch(failed);
    if (!added) return;
    await loadBots();
    await openBot(added);
  }

  function toggleStudio(): void {
    if (page === "studio") {
      page = lastBotPage;
    } else {
      lastBotPage = page;
      page = "studio";
    }
  }

  function changeStudio(key: string, value: unknown): void {
    request("settings.set", { key, value }).catch(failed);
    if (key === "studio.effects") applyEffects();
  }

  function applyEffects(): void {
    document.documentElement.dataset.effects = studio.effects ? "on" : "off";
  }

  async function loadStudio(): Promise<void> {
    const keys = ["studio.picker", "studio.effects", "studio.closing", "studio.collapse_on_run", "studio.pill_hide_after"];
    const found = await Promise.all(keys.map((key) => request("settings.get", { key }).catch(() => null)));
    studio.picker = found[0] === "sidebar" ? "sidebar" : "dropdown";
    studio.effects = found[1] !== false;
    studio.closing = found[2] === "quit" ? "quit" : "tray";
    studio.collapseOnRun = found[3] !== false;
    studio.pillHideAfter = "3";
    if (found[4] === 0) studio.pillHideAfter = "never";
    else if (typeof found[4] === "number") studio.pillHideAfter = String(found[4]);
    applyEffects();
  }

  $effect(() => {
    if (!connected) return;
    loadStudio();
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
      if (bot?.path === data.path && page === "overview") loadPage().catch(failed);
    });
    const stopPage = on("studio.page", (data) => {
      if (data.page === "studio-settings" && page !== "studio") toggleStudio();
    });
    return () => {
      stopStatus();
      stopChanged();
      stopPage();
    };
  });

  $effect(() => {
    page; // reload when the page changes
    if (connected && bot) loadPage().catch(failed);
  });

  register({ name: "palette.open", label: "Commands", run: () => (palette = true) });
  register({ name: "hub.section.next", label: "Next page", run: () => (page = PAGES[(PAGES.findIndex((each) => each.value === page) + 1) % PAGES.length].value) });
  register({ name: "studio.overview", label: "Go to Overview", run: () => (page = "overview") });
  register({ name: "studio.results", label: "Go to Results", run: () => (page = "results") });
  register({ name: "studio.library", label: "Go to Library", run: () => (page = "library") });
  register({ name: "studio.settings", label: "Go to Settings", run: () => (page = "settings") });
  register({ name: "hub.run.toggle", label: "Run or stop the bot", run: () => control(live ? "project.stop" : "project.run") });
  register({ name: "run.pause", label: "Pause the bot", run: () => control("project.pause") });
</script>

<div class="studio" class:with-sidebar={studio.picker === "sidebar"}>
  {#if studio.picker === "sidebar"}
    <BotPicker {bots} {bot} variant="sidebar" onpick={openBot} onadd={addFolder} onstudio={toggleStudio} studioOpen={page === "studio"} />
  {/if}
  <div class="main">
    <header class="top">
      <div class="left">
        {#if studio.picker !== "sidebar"}
          <BotPicker {bots} {bot} onpick={openBot} onadd={addFolder} onstudio={toggleStudio} studioOpen={page === "studio"} />
        {/if}
      </div>
      <Segmented items={PAGES} bind:value={() => botPage, (next) => (page = next)} label="Bot pages" variant="nav" />
      <div class="right">
        <div class="controls" role="group" aria-label="Bot controls">
          <span class="state" data-status={status}><span class="dot"></span>{status === "paused" ? "Paused" : live ? "Running" : "Stopped"}</span>
          <button class="ctl go" class:on={status === "running"} aria-label="Run" title="Run (F5)" disabled={!bot || live || status === "broken"} onclick={() => control("project.run")}>▶</button>
          <button class="ctl" class:on={status === "paused"} aria-label={status === "paused" ? "Resume" : "Pause"} title="Pause (Ctrl+Alt+P)" disabled={!live} onclick={() => control("project.pause")}>❚❚</button>
          <button class="ctl" aria-label="Stop" title="Stop (Ctrl+Alt+Q)" disabled={!live} onclick={() => control("project.stop")}>■</button>
          <span class="sep"></span>
          <button class="edit" class:on={editing} aria-pressed={editing} onclick={() => (editing = !editing)}>✎ {editing ? "Editing" : "Edit"}</button>
        </div>
      </div>
    </header>

    {#key page + (bot?.path ?? "")}
      <main class="page-in">
        {#if page === "studio"}
          <StudioSettings bind:values={studio} onchange={changeStudio} />
        {:else if !connected}
          <p class="empty">darbit Studio needs darbit's local server. Start it with <code>darbit app</code>.</p>
        {:else if problem}
          <p class="empty">{problem}</p>
        {:else if !ready}
          <span></span>
        {:else if !bot}
          <p class="empty">No bots yet. Install one with <code>darbit install &lt;link&gt;</code>, or add a bot folder from the bot menu.</p>
        {:else if page === "overview"}
          <OverviewPage bot={bot.name} {tiles} running={status} onsetup={() => openTool("guide")} onretake={() => openTool("capture")} />
        {:else if page === "library"}
          <LibraryPage path={bot.path} {editing} oncapture={() => openTool("capture")} />
        {:else if page === "results"}
          <ResultsPage path={bot.path} onretake={() => openTool("capture")} />
        {:else if page === "settings"}
          {#if form.error}
            <p class="empty bad">{form.error}</p>
          {:else if form.sections.length}
            <BotSettingsPage sections={form.sections} values={form.values} onsave={saveSettings} />
          {:else if !loading}
            <p class="empty">This bot has no settings.toml.</p>
          {/if}
        {/if}
      </main>
    {/key}
  </div>
  <CommandPalette bind:open={palette} />
  <Toast />
</div>

<style>
  :global(html body) {
    margin: 0;
    background:
      radial-gradient(60vw 40vh at 80% -10%, color-mix(in oklab, var(--accent) 16%, transparent), transparent 70%),
      radial-gradient(50vw 40vh at 0% 100%, color-mix(in oklab, var(--accent-2) 14%, transparent), transparent 70%),
      var(--bg);
    background-attachment: fixed;
  }
  /* "Smooth effects" off: no blur and no motion, for slower PCs */
  :global(html[data-effects="off"] *),
  :global(html[data-effects="off"] *::before),
  :global(html[data-effects="off"] *::after) {
    backdrop-filter: none !important;
    animation: none !important;
    transition: none !important;
  }
  .studio {
    display: flex;
    min-height: 100vh;
    color: var(--text);
    font-size: var(--size-content);
  }
  .main {
    flex: 1;
    min-width: 0;
    display: grid;
    grid-template-rows: auto 1fr;
    gap: var(--space-l);
    padding: var(--space-l) var(--space-xxl) var(--space-xxl);
  }
  .top {
    display: grid;
    grid-template-columns: 1fr auto 1fr;
    align-items: center;
    gap: var(--space-m);
    position: relative;
    z-index: 10;
  }
  .left {
    display: flex;
    justify-self: start;
  }
  .right {
    display: flex;
    justify-self: end;
  }
  .controls {
    display: flex;
    align-items: center;
    gap: var(--space-xs);
    padding: var(--space-xs);
    border-radius: var(--radius-pill);
    background: var(--glass);
    backdrop-filter: blur(var(--blur));
    border: 1px solid var(--line);
    box-shadow: var(--shadow);
  }
  .state {
    display: inline-flex;
    align-items: center;
    gap: var(--space-s);
    padding: 0 var(--space-s) 0 var(--space-m);
    font: 600 var(--size-caption) / 1 var(--font-strong);
    color: var(--muted);
    white-space: nowrap;
  }
  .state .dot {
    width: var(--space-s);
    height: var(--space-s);
    border-radius: 50%;
    background: var(--faint);
  }
  .state[data-status="running"] .dot {
    background: var(--ok);
    box-shadow: 0 0 var(--space-s) var(--ok);
  }
  .state[data-status="paused"] .dot {
    background: var(--warn);
  }
  .ctl {
    width: var(--control-m);
    height: var(--control-m);
    display: grid;
    place-items: center;
    border: 0;
    border-radius: 50%;
    background: var(--raised);
    color: var(--text);
    font-size: var(--size-caption);
    cursor: pointer;
    transition:
      background var(--duration-fast) var(--curve-easy-ease),
      transform var(--duration-fast) var(--curve-easy-ease);
  }
  .ctl:hover:not(:disabled) {
    background: var(--raised-hover);
  }
  .ctl:active:not(:disabled) {
    transform: scale(0.94);
  }
  .ctl:disabled {
    opacity: 0.35;
    cursor: default;
  }
  .ctl.go:not(:disabled) {
    background: var(--accent);
    color: var(--on-accent);
  }
  .ctl.on {
    box-shadow: 0 0 0 2px color-mix(in oklab, var(--accent) 50%, transparent);
  }
  .sep {
    width: 1px;
    height: var(--space-xl);
    background: var(--line);
    margin: 0 var(--space-xs);
  }
  .edit {
    height: var(--control-m);
    padding: 0 var(--space-m);
    border: 0;
    border-radius: var(--radius-pill);
    background: var(--raised);
    color: var(--text);
    font: 650 var(--size-caption) / 1 var(--font-strong);
    white-space: nowrap;
    cursor: pointer;
    transition: background var(--duration-fast) var(--curve-easy-ease);
  }
  .edit:hover {
    background: var(--raised-hover);
  }
  .edit.on {
    background: var(--accent-2);
    color: var(--on-accent);
  }
  main {
    min-width: 0;
  }
  .page-in {
    animation: page-in var(--duration-normal) var(--curve-decelerate);
  }
  @keyframes page-in {
    from {
      opacity: 0;
      transform: translateY(var(--space-s));
    }
  }
  .empty {
    color: var(--muted);
    margin: var(--space-xxl) auto;
    text-align: center;
  }
  .bad {
    color: var(--danger);
  }
</style>
