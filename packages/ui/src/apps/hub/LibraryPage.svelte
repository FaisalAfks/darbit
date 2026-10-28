<!-- The Library page: everything the bot uses (decision 0013, round 4). A grid grouped by screen with filters,
     cards with a score meter, and an inspector for the chosen asset: its numbers, where it's used, and, with
     Edit on, Retake and a Rename that previews every line it changes before changing them all at once. -->
<script lang="ts" module>
  // the last list per bot, so coming back to the Library shows it at once while it checks for changes
  const remembered = new Map<string, { assets: unknown[]; screens: unknown[] }>();
</script>

<script lang="ts">
  import { on, request } from "$lib/api";
  import Segmented from "$lib/components/Segmented.svelte";
  import { toast } from "$lib/toasts.svelte";
  import ActionsTab from "./ActionsTab.svelte";

  interface Asset {
    name: string;
    kind: "image" | "region" | "point";
    group: string;
    thumbnail: string | null;
    version?: string; // an image's file version; the server skips thumbnails the page already has
    same?: boolean;
    size: number[] | null;
    region?: number[] | null;
    location?: number[] | null;
    similarity?: number | null;
    scores: number[];
    missing: boolean;
    uses: number;
  }
  interface Use {
    file: string;
    line: number;
    text: string;
  }
  interface Plan {
    old: string;
    new: string;
    files: { from: string; to: string }[];
    lines: { file: string; line: number; before: string; after: string }[];
  }

  let {
    path,
    editing,
    oncapture,
    ontest,
    tab = $bindable("assets"),
    opened = $bindable(""),
  }: {
    path: string;
    editing: boolean;
    oncapture: (name?: string, kind?: string) => void;
    ontest: (name: string) => void;
    tab?: string;
    opened?: string;
  } = $props();

  const TABS = [
    { value: "assets", label: "Assets" },
    { value: "actions", label: "Actions" },
  ];

  const NEEDS = 0.8; // the similarity an image needs when it doesn't say
  const FILTERS = [
    { value: "all", label: "All" },
    { value: "image", label: "Images" },
    { value: "region", label: "Regions" },
    { value: "point", label: "Points" },
    { value: "missing", label: "Missing" },
    { value: "weak", label: "Weak" },
  ];

  interface ScreenShot {
    screen: string;
    picture: string;
    w: number;
    h: number;
    assets: Record<string, { kind: string; box: number[] }>;
  }

  let assets: Asset[] = $state([]);
  let screens: ScreenShot[] = $state([]);
  let view = $state("grid"); // grid or screen
  let screenName = $state("");
  let loaded = $state(false);
  let filter = $state("all");
  let query = $state("");
  let chosen: string | null = $state(null);
  let uses: Use[] = $state([]);
  let renaming = $state(false);
  let newName = $state("");
  let plan = $state<Plan | null>(null);
  let planError = $state("");

  const current = $derived(assets.find((asset) => asset.name === chosen) ?? null);
  const shownScreen = $derived(screens.find((each) => each.screen === screenName) ?? screens[0] ?? null);
  const currentPlace = $derived(placeOf(current));
  const thumbnails = $derived(Object.fromEntries(assets.filter((asset) => asset.thumbnail).map((asset) => [asset.name, asset.thumbnail as string])));
  const shown = $derived(assets.filter(keep));
  const groups = $derived(groupAssets(shown));
  const counts = $derived(countKinds(assets));

  function needs(asset: Asset): number {
    return asset.similarity ?? NEEDS;
  }

  function last(asset: Asset): number | null {
    return asset.scores.length ? asset.scores[asset.scores.length - 1] : null;
  }

  function weak(asset: Asset): boolean {
    const score = last(asset);
    return score !== null && score < needs(asset);
  }

  function keep(asset: Asset): boolean {
    if (query && !asset.name.toLowerCase().includes(query.toLowerCase())) return false;
    if (filter === "all") return true;
    if (filter === "missing") return asset.missing;
    if (filter === "weak") return weak(asset);
    return asset.kind === filter && !asset.missing;
  }

  function groupAssets(list: Asset[]): { name: string; assets: Asset[] }[] {
    const found: Record<string, Asset[]> = {};
    for (const asset of list) {
      if (!found[asset.group]) found[asset.group] = [];
      found[asset.group].push(asset);
    }
    return Object.keys(found)
      .sort()
      .map((name) => ({ name, assets: found[name] }));
  }

  function countKinds(list: Asset[]): Record<string, number> {
    const found: Record<string, number> = { all: list.length, image: 0, region: 0, point: 0, missing: 0, weak: 0 };
    for (const asset of list) {
      if (asset.missing) found.missing += 1;
      else found[asset.kind] += 1;
      if (weak(asset)) found.weak += 1;
    }
    return found;
  }

  function placeOf(asset: Asset | null): { shot: ScreenShot; box: number[] } | null {
    if (!asset) return null;
    for (const shot of screens) {
      const place = shot.assets[asset.name];
      if (place) return { shot, box: place.box };
    }
    return null;
  }

  function pct(value: number, total: number): string {
    return `${(value / total) * 100}%`;
  }

  async function load(): Promise<void> {
    const before = remembered.get(path);
    if (before && !assets.length) {
      assets = before.assets as Asset[];
      screens = before.screens as ScreenShot[];
      loaded = true;
    }
    const [found, shots] = await Promise.all([
      request<Asset[]>("library.list", { path, have: versions() }),
      request<ScreenShot[]>("library.screens", { path }).catch(() => []),
    ]);
    assets = withThumbnails(found);
    screens = shots;
    loaded = true;
    remembered.set(path, { assets, screens });
    if (chosen && !assets.some((asset) => asset.name === chosen)) chosen = null;
  }

  /** Just these assets again (after a retake or a delete), merged into the list. */
  async function refresh(names: string[]): Promise<void> {
    const found = withThumbnails(await request<Asset[]>("library.list", { path, names, have: versions() }));
    const byName = new Map(found.map((asset) => [asset.name, asset]));
    const kept = assets.filter((asset) => !names.includes(asset.name) || byName.has(asset.name)).map((asset) => byName.get(asset.name) ?? asset);
    for (const asset of found) if (!kept.some((each) => each.name === asset.name)) kept.push(asset);
    assets = kept.sort((a, b) => (a.name < b.name ? -1 : 1));
    screens = await request<ScreenShot[]>("library.screens", { path }).catch(() => screens);
    remembered.set(path, { assets, screens });
  }

  function versions(): Record<string, string> {
    const found: Record<string, string> = {};
    for (const asset of assets) if (asset.version && asset.thumbnail) found[asset.name] = asset.version;
    return found;
  }

  /** The server leaves out thumbnails the page already has (`same`): keep those. */
  function withThumbnails(found: Asset[]): Asset[] {
    const old = new Map(assets.map((asset) => [asset.name, asset]));
    return found.map((asset) => (asset.same ? { ...asset, thumbnail: old.get(asset.name)?.thumbnail ?? null, size: old.get(asset.name)?.size ?? null } : asset));
  }

  let deleting = $state(false); // Delete asks once more

  async function deleteAsset(): Promise<void> {
    if (!current) return;
    if (!deleting) {
      deleting = true;
      return;
    }
    deleting = false;
    const name = current.name;
    try {
      await request("library.delete", { path, name });
      toast(current.uses ? `Deleted ${name}: ${current.uses} line${current.uses === 1 ? "" : "s"} still use it` : `Deleted ${name}`);
      await refresh([name]);
      if (!assets.some((asset) => asset.name === name)) chosen = null;
    } catch (error) {
      toast((error as Error).message);
    }
  }

  async function choose(name: string): Promise<void> {
    chosen = chosen === name ? null : name;
    renaming = false;
    plan = null;
    uses = [];
    if (chosen) uses = await request<Use[]>("library.uses", { path, name: chosen }).catch(() => []);
  }

  async function preview(): Promise<void> {
    planError = "";
    plan = null;
    if (!current || !newName.trim()) return;
    try {
      plan = await request<Plan>("library.rename.plan", { path, name: current.name, to: newName.trim() });
    } catch (error) {
      planError = (error as Error).message;
    }
  }

  async function confirmRename(): Promise<void> {
    if (!plan) return;
    try {
      await request("library.rename", { path, name: plan.old, to: plan.new });
      toast(`Renamed ${plan.old} to ${plan.new} in ${plan.lines.length} place${plan.lines.length === 1 ? "" : "s"}`);
      chosen = plan.new;
      renaming = false;
      plan = null;
      await load();
      uses = await request<Use[]>("library.uses", { path, name: chosen });
    } catch (error) {
      toast((error as Error).message);
    }
  }

  function meter(asset: Asset): { width: number; tick: number; tone: string } {
    const score = last(asset) ?? 0;
    const tone = weak(asset) ? "var(--danger)" : score >= needs(asset) + 0.05 ? "var(--ok)" : "var(--warn)";
    return { width: score * 100, tick: needs(asset) * 100, tone };
  }

  $effect(() => {
    path;
    chosen = null;
    load().catch((error: Error) => toast(error.message));
  });

  $effect(() => {
    // a retake or a new picture from Capture: redraw just those cards
    return on("library.changed", (data: { path: string; names: string[] }) => {
      if (data.path === path) refresh(data.names).catch(() => {});
    });
  });

  $effect(() => {
    if (!editing) {
      renaming = false;
      plan = null;
    }
  });
  function score(value: number | null | undefined): string {
    if (value === null || value === undefined) return "";
    if (value >= 0.995) return "1.00";
    return value.toFixed(2).slice(1); // .97
  }

</script>

{#if !opened}
  <div class="tabs"><Segmented items={TABS} bind:value={tab} label="Library" /></div>
{/if}

{#if tab === "actions"}
  <ActionsTab {path} {editing} {thumbnails} bind:opened />
{:else}
<div class="library" class:has-current={!!current}>
  <div class="main">
    <div class="bar">
      <div class="views" role="radiogroup" aria-label="View">
        <button role="radio" aria-checked={view === "grid"} class:on={view === "grid"} onclick={() => (view = "grid")}>▦ Grid</button>
        <button role="radio" aria-checked={view === "screen"} class:on={view === "screen"} onclick={() => (view = "screen")} disabled={!screens.length} title={screens.length ? "" : "Screens show up once pictures are taken with Capture"}>▣ Screen</button>
      </div>
      <input class="search" bind:value={query} placeholder="⌕ Search {assets.length} assets" aria-label="Search assets" />
      <div class="filters" role="radiogroup" aria-label="Show">
        {#each FILTERS as item (item.value)}
          <button role="radio" aria-checked={filter === item.value} class:on={filter === item.value} data-kind={item.value} onclick={() => (filter = item.value)}>
            {item.label}<small>{counts[item.value]}</small>
          </button>
        {/each}
      </div>
      <span class="grow"></span>
      {#if editing}
        <button class="action primary" onclick={() => oncapture()}>▣ Capture</button>
      {:else}
        <span class="hint">✎ Edit to add, retake or rename</span>
      {/if}
    </div>

    {#if loaded && !shown.length}
      <p class="empty">{assets.length ? "Nothing matches." : "No assets yet. Turn on Edit and use Capture, or the setup guide."}</p>
    {/if}

    {#if view === "screen" && shownScreen}
      <div class="screenpick">
        {#each screens as shot (shot.screen)}<button class:on={shot.screen === shownScreen.screen} onclick={() => (screenName = shot.screen)}>{shot.screen}</button>{/each}
      </div>
      <div class="screen">
        <img src={shownScreen.picture} alt="The {shownScreen.screen} screen, when its pictures were taken" />
        {#each Object.entries(shownScreen.assets) as [assetName, place] (assetName)}
          <button
            class="placed"
            class:chosen={assetName === chosen}
            data-kind={place.kind}
            style:left={pct(place.box[0], shownScreen.w)}
            style:top={pct(place.box[1], shownScreen.h)}
            style:width={pct(place.box[2], shownScreen.w)}
            style:height={pct(place.box[3], shownScreen.h)}
            onclick={() => choose(assetName)}
            title={assetName}
          ><span>{assetName.slice(shownScreen.screen.length + 1) || assetName}</span></button>
        {/each}
      </div>
    {:else}
    {#each groups as group (group.name)}
      <h3>{group.name}<small>{group.assets.length}</small></h3>
      <div class="grid">
        {#each group.assets as asset (asset.name)}
          {@const m = meter(asset)}
          <button
            class="card"
            class:chosen={asset.name === chosen}
            class:faded={!!chosen && asset.name !== chosen}
            class:missing={asset.missing}
            onclick={() => choose(asset.name)}
            title={asset.name}
          >
            <span class="thumb" data-kind={asset.kind}>
              {#if asset.thumbnail}<img src={asset.thumbnail} alt="" />{:else if asset.missing}not taken{:else if asset.kind === "region"}▭ {asset.region ? `${asset.region[2]} × ${asset.region[3]}` : ""}{:else}✛ {asset.location ? `${asset.location[0]}, ${asset.location[1]}` : ""}{/if}
              {#if asset.region && asset.kind === "image"}<span class="regionchip">▭</span>{/if}
            </span>
            <span class="name">{asset.name.slice(group.name.length + 1) || asset.name}{#if weak(asset)} ⚠{/if}</span>
            {#if asset.kind === "image" && last(asset) !== null}
              <span class="meter" style:--tone={m.tone}><i style:width="{m.width}%"></i><b style:left="{m.tick}%"></b></span>
            {/if}
            <span class="meta">
              {#if asset.missing}<span class="bad">in the guide</span>{:else if asset.kind === "image"}<span>{last(asset) !== null ? score(last(asset)) : "not checked"}</span>{:else}<span class="kind" data-kind={asset.kind}>{asset.kind}</span>{/if}
              <span class="grow"></span><span>{asset.uses ? `used ${asset.uses}×` : "unused"}</span>
            </span>
          </button>
        {/each}
      </div>
    {/each}
    {/if}
  </div>

  {#if current}
    <aside class="inspector">
      {#if currentPlace}
        <div class="inplace" style:aspect-ratio="{currentPlace.shot.w} / {currentPlace.shot.h}">
          <img src={currentPlace.shot.picture} alt="" />
          <span class="glow" style:left={pct(currentPlace.box[0], currentPlace.shot.w)} style:top={pct(currentPlace.box[1], currentPlace.shot.h)} style:width={pct(currentPlace.box[2], currentPlace.shot.w)} style:height={pct(currentPlace.box[3], currentPlace.shot.h)}></span>
          <small>{currentPlace.shot.screen}</small>
        </div>
      {/if}
      <div class="big" data-kind={current.kind}>
        {#if current.thumbnail}<img src={current.thumbnail} alt="" />{:else if current.missing}not taken yet{:else if current.kind === "region"}▭{:else}✛{/if}
      </div>
      <h2>{current.name}<span class="kind" data-kind={current.kind}>{current.missing ? "missing" : current.kind}</span></h2>
      <dl>
        {#if current.size}<dt>Size</dt><dd>{current.size[0]} × {current.size[1]}</dd>{/if}
        {#if current.kind === "image"}<dt>Needs</dt><dd>{score(needs(current))}</dd>{/if}
        {#if last(current) !== null}<dt>Last score</dt><dd class:bad={weak(current)}>{score(last(current))}</dd>{/if}
        {#if current.region}<dt>Searched in</dt><dd>{current.region.join(", ")}</dd>{/if}
        {#if current.location}<dt>Point</dt><dd>{current.location.join(", ")}</dd>{/if}
      </dl>
      {#if current.scores.length > 1}
        <div class="history" aria-label="Last checks">
          {#each current.scores as score, index (index)}<i class:low={score < needs(current)} style:height="{Math.max(8, score * 100)}%"></i>{/each}
        </div>
      {/if}

      {#if current.kind === "image" && !current.missing}
        <div class="actions"><button class="action test" onclick={() => ontest(current?.name ?? "")}>◎ Test on screen</button></div>
      {/if}
      {#if editing}
        <div class="actions">
          <button class="action" onclick={() => oncapture(current?.name, current?.kind)}>▣ {current.missing ? "Take it" : "Retake"}</button>
          {#if !current.missing}<button class="action" class:on={renaming} onclick={() => { renaming = !renaming; newName = current?.name ?? ""; plan = null; planError = ""; }}>✎ Rename</button>{/if}
          {#if !current.missing}<button class="action bad" onclick={deleteAsset} onblur={() => (deleting = false)} title="Delete its picture and settings">{deleting ? (current.uses ? `Used in ${current.uses} place${current.uses === 1 ? "" : "s"}: delete?` : `Delete ${current.name}?`) : "🗑 Delete"}</button>{/if}
        </div>
      {/if}

      {#if renaming}
        <form class="rename" onsubmit={(event) => { event.preventDefault(); preview(); }}>
          <label for="new-name">New name</label>
          <input id="new-name" bind:value={newName} spellcheck="false" />
          <button class="action" type="submit">Show what changes</button>
          {#if planError}<p class="bad">{planError}</p>{/if}
          {#if plan}
            <div class="diff">
              {#each plan.files as file (file.from)}<div><span class="del">{file.from}</span> → <span class="add">{file.to}</span></div>{/each}
              {#each plan.lines as line (line.file + line.line)}
                <div class="where">{line.file}:{line.line}</div>
                <div class="del">- {line.before}</div>
                <div class="add">+ {line.after}</div>
              {/each}
            </div>
            <button class="action primary" type="button" onclick={confirmRename}>Rename in {plan.lines.length + plan.files.length} place{plan.lines.length + plan.files.length === 1 ? "" : "s"}</button>
          {/if}
        </form>
      {/if}

      <div class="uses">
        <b>{uses.length ? `Used in ${uses.length} place${uses.length === 1 ? "" : "s"}` : "Not used in the bot's code"}</b>
        {#each uses.slice(0, 12) as use (use.file + use.line)}<code title={use.text}>{use.file}:{use.line}</code>{/each}
      </div>
    </aside>
  {/if}
</div>

{/if}

<style>
  .views {
    display: flex;
    padding: var(--space-xxs);
    border-radius: var(--radius-pill);
    background: var(--raised);
  }
  .views button,
  .screenpick button {
    height: calc(var(--control-m) - 2 * var(--space-xxs));
    padding: 0 var(--space-m);
    border: 0;
    border-radius: var(--radius-pill);
    background: none;
    color: var(--muted);
    font: 600 var(--size-caption) / 1 var(--font-strong);
    cursor: pointer;
  }
  .views button.on,
  .screenpick button.on {
    background: var(--raised-hover);
    color: var(--text);
  }
  .views button:disabled {
    opacity: 0.4;
    cursor: default;
  }
  .screenpick {
    display: flex;
    gap: var(--space-xs);
    flex-wrap: wrap;
  }
  .screenpick button {
    height: var(--control-m);
    background: var(--raised);
  }
  .screen {
    position: relative;
    border-radius: var(--radius-l);
    overflow: hidden;
    border: 1px solid var(--line);
    animation: page-in var(--duration-normal) var(--curve-decelerate);
  }
  .screen img {
    display: block;
    width: 100%;
  }
  .placed {
    position: absolute;
    padding: 0;
    border: 2px solid color-mix(in oklab, var(--kind-image) 70%, transparent);
    border-radius: var(--radius-s);
    background: color-mix(in oklab, var(--kind-image) 8%, transparent);
    cursor: pointer;
    transition:
      box-shadow var(--duration-normal) var(--curve-decelerate),
      background var(--duration-fast) var(--curve-easy-ease);
  }
  .placed span {
    position: absolute;
    left: calc(-1 * var(--space-xxs));
    bottom: 100%;
    padding: 0 var(--space-s);
    border-radius: var(--radius-s) var(--radius-s) var(--radius-s) 0;
    background: var(--kind-image);
    color: var(--on-accent);
    font: 700 var(--size-caption) / 1.5 var(--font-strong);
    white-space: nowrap;
  }
  .placed[data-kind="region"] {
    border-style: dashed;
    border-color: var(--kind-region);
    background: none;
  }
  .placed[data-kind="region"] span {
    background: var(--kind-region);
  }
  .placed[data-kind="location"] {
    border-color: var(--kind-point);
    border-radius: 50%;
  }
  .placed[data-kind="location"] span {
    background: var(--kind-point);
  }
  .placed:hover {
    background: color-mix(in oklab, var(--kind-image) 18%, transparent);
  }
  .placed.chosen {
    z-index: 1;
    border-color: var(--kind-image);
    box-shadow:
      0 0 0 100vmax color-mix(in oklab, var(--bg) 45%, transparent),
      0 0 var(--space-xl) color-mix(in oklab, var(--kind-image) 60%, transparent);
  }
  .inplace {
    position: relative;
    border-radius: var(--radius-m);
    overflow: hidden;
  }
  .inplace img {
    position: absolute;
    inset: 0;
    width: 100%;
    height: 100%;
  }
  .inplace .glow {
    position: absolute;
    border: 2px solid var(--kind-image);
    border-radius: var(--radius-s);
    box-shadow:
      0 0 0 100vmax color-mix(in oklab, var(--bg) 45%, transparent),
      0 0 var(--space-l) color-mix(in oklab, var(--kind-image) 70%, transparent);
  }
  .inplace .glow::after {
    content: "";
    position: absolute;
    inset: calc(-1 * var(--space-xs));
    border-radius: var(--radius-m);
    box-shadow: 0 0 var(--space-xl) var(--kind-image);
    animation: breathe 1.6s ease-in-out infinite;
  }
  .inplace small {
    position: absolute;
    left: var(--space-s);
    bottom: var(--space-s);
    padding: 0 var(--space-s);
    border-radius: var(--radius-pill);
    background: color-mix(in oklab, var(--bg) 70%, transparent);
    font-size: var(--size-caption);
  }
  .action.test {
    border: 1px solid color-mix(in oklab, var(--ok) 40%, transparent);
    background: color-mix(in oklab, var(--ok) 14%, transparent);
    color: var(--ok);
  }
  @keyframes breathe {
    50% {
      opacity: 0.35;
    }
  }
  @keyframes page-in {
    from {
      opacity: 0;
      transform: translateY(var(--space-s));
    }
  }
  .tabs {
    margin-bottom: var(--space-m);
  }
  .library {
    display: grid;
    grid-template-columns: 1fr;
    gap: var(--space-l);
    align-items: start;
  }
  .library.has-current {
    grid-template-columns: 1fr var(--width-inspector);
  }
  .main {
    min-width: 0;
    display: grid;
    gap: var(--space-m);
  }
  .bar {
    display: flex;
    align-items: center;
    gap: var(--space-m);
    flex-wrap: wrap;
  }
  .search {
    min-width: calc(6 * var(--control-l));
    height: var(--control-m);
    padding: 0 var(--space-l);
    border: 1px solid var(--line);
    border-radius: var(--radius-pill);
    background: var(--glass);
    color: var(--text);
    font: inherit;
    font-size: var(--size-body);
  }
  .search:focus {
    outline: none;
    border-color: var(--accent);
  }
  .filters {
    display: flex;
    gap: var(--space-xs);
    flex-wrap: wrap;
  }
  .filters button {
    display: inline-flex;
    align-items: center;
    gap: var(--space-s);
    height: var(--control-m);
    padding: 0 var(--space-m);
    border: 0;
    border-radius: var(--radius-pill);
    background: var(--raised);
    color: var(--muted);
    font: 600 var(--size-caption) / 1 var(--font-strong);
    cursor: pointer;
    transition: background var(--duration-fast) var(--curve-easy-ease), color var(--duration-fast) var(--curve-easy-ease);
  }
  .filters button small {
    color: var(--faint);
  }
  .filters button.on {
    background: var(--raised-hover);
    color: var(--text);
  }
  .filters [data-kind="missing"] {
    color: var(--danger);
  }
  .filters [data-kind="weak"] {
    color: var(--warn);
  }
  .grow {
    flex: 1;
  }
  .hint {
    color: var(--muted);
    font-size: var(--size-caption);
  }
  .action {
    height: var(--control-m);
    padding: 0 var(--space-l);
    border: 0;
    border-radius: var(--radius-pill);
    background: var(--raised);
    color: var(--text);
    font: 650 var(--size-caption) / 1 var(--font-strong);
    cursor: pointer;
    white-space: nowrap;
    transition: background var(--duration-fast) var(--curve-easy-ease);
  }
  .action:hover {
    background: var(--raised-hover);
  }
  .action.primary {
    background: var(--accent);
    color: var(--on-accent);
  }
  .action.on {
    background: var(--accent-2);
    color: var(--on-accent);
  }
  h3 {
    margin: var(--space-s) 0 0;
    display: flex;
    gap: var(--space-s);
    align-items: baseline;
    font: 700 var(--size-caption) / 1 var(--font-strong);
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: var(--muted);
  }
  h3 small {
    color: var(--faint);
  }
  .grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(calc(5 * var(--control-l)), 1fr));
    gap: var(--space-m);
  }
  .card {
    position: relative;
    display: grid;
    gap: var(--space-s);
    padding: var(--space-s);
    border: 1px solid transparent;
    border-radius: var(--radius-l);
    background: var(--glass);
    color: var(--text);
    font: inherit;
    text-align: left;
    cursor: pointer;
    transition:
      transform var(--duration-normal) var(--curve-decelerate),
      box-shadow var(--duration-normal) var(--curve-decelerate),
      opacity var(--duration-normal) var(--curve-easy-ease),
      border-color var(--duration-fast) var(--curve-easy-ease);
  }
  .card:hover {
    transform: translateY(calc(-1 * var(--space-xxs)));
    border-color: var(--line);
  }
  .card.chosen {
    transform: translateY(calc(-1 * var(--space-xs))) scale(1.03);
    border-color: var(--accent);
    background: color-mix(in oklab, var(--accent) 10%, var(--glass));
    box-shadow: 0 0 0 var(--space-xxs) color-mix(in oklab, var(--accent) 22%, transparent), var(--shadow), 0 0 var(--space-xxl) color-mix(in oklab, var(--accent) 30%, transparent);
    z-index: 1;
  }
  .card.chosen::after {
    content: "✓";
    position: absolute;
    top: calc(-1 * var(--space-s));
    right: calc(-1 * var(--space-s));
    width: var(--space-xl);
    height: var(--space-xl);
    display: grid;
    place-items: center;
    border-radius: 50%;
    background: var(--accent);
    color: var(--on-accent);
    font: 800 var(--size-caption) / 1 var(--font-strong);
  }
  .card.faded {
    opacity: 0.6;
  }
  .thumb,
  .big {
    position: relative;
    display: grid;
    place-items: center;
    height: calc(2 * var(--control-l));
    border-radius: var(--radius-m);
    background: var(--raised);
    color: var(--muted);
    font: 600 var(--size-caption) / 1 var(--font-strong);
    overflow: hidden;
  }
  .thumb img,
  .big img {
    max-width: 100%;
    max-height: 100%;
    object-fit: contain;
  }
  .thumb[data-kind="region"],
  .big[data-kind="region"] {
    background: color-mix(in oklab, var(--kind-region) 14%, transparent);
    color: var(--kind-region);
  }
  .thumb[data-kind="point"],
  .big[data-kind="point"] {
    background: color-mix(in oklab, var(--kind-point) 12%, transparent);
    color: var(--kind-point);
  }
  .missing .thumb {
    background: repeating-linear-gradient(45deg, color-mix(in oklab, var(--danger) 14%, transparent) 0 var(--space-s), transparent var(--space-s) var(--space-l));
    color: var(--danger);
    border: 1px dashed color-mix(in oklab, var(--danger) 50%, transparent);
  }
  .regionchip {
    position: absolute;
    top: var(--space-xs);
    right: var(--space-xs);
    padding: 0 var(--space-s);
    border-radius: var(--radius-pill);
    background: color-mix(in oklab, var(--bg) 70%, transparent);
    color: var(--kind-region);
  }
  .name {
    font: 650 var(--size-caption) / var(--line-caption) var(--font-strong);
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }
  .meter {
    position: relative;
    height: var(--space-xs);
    border-radius: var(--radius-pill);
    background: var(--raised);
  }
  .meter i {
    position: absolute;
    inset: 0 auto 0 0;
    border-radius: var(--radius-pill);
    background: var(--tone);
  }
  .meter b {
    position: absolute;
    top: calc(-1 * var(--space-xxs));
    bottom: calc(-1 * var(--space-xxs));
    width: 2px;
    border-radius: 2px;
    background: var(--text);
    opacity: 0.75;
  }
  .meta {
    display: flex;
    align-items: center;
    gap: var(--space-s);
    color: var(--muted);
    font-size: var(--size-caption);
  }
  .kind {
    padding: 0 var(--space-s);
    border-radius: var(--radius-pill);
    font: 700 var(--size-caption) / var(--line-caption) var(--font-strong);
    text-transform: uppercase;
    color: var(--kind-image);
    background: color-mix(in oklab, var(--kind-image) 15%, transparent);
  }
  .kind[data-kind="region"] {
    color: var(--kind-region);
    background: color-mix(in oklab, var(--kind-region) 15%, transparent);
  }
  .kind[data-kind="point"] {
    color: var(--kind-point);
    background: color-mix(in oklab, var(--kind-point) 15%, transparent);
  }
  .bad {
    color: var(--danger);
  }
  .inspector {
    position: sticky;
    top: var(--space-l);
    display: grid;
    gap: var(--space-m);
    padding: var(--space-l);
    border-radius: var(--radius-xl);
    background: var(--glass);
    border: 1px solid var(--line);
    animation: slide-in var(--duration-normal) var(--curve-decelerate);
    max-height: calc(100vh - 6 * var(--space-xl));
    overflow: auto;
  }
  .big {
    height: calc(4 * var(--control-l));
  }
  h2 {
    margin: 0;
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: var(--space-s);
    font: 700 var(--size-subtitle) / var(--line-subtitle) var(--font-strong);
    word-break: break-all;
  }
  dl {
    display: grid;
    grid-template-columns: auto 1fr;
    gap: var(--space-xs) var(--space-l);
    margin: 0;
    font-size: var(--size-body);
  }
  dt {
    color: var(--muted);
  }
  dd {
    margin: 0;
    font-weight: 650;
  }
  .history {
    display: flex;
    align-items: end;
    gap: var(--space-xxs);
    height: var(--space-xxl);
  }
  .history i {
    flex: 1;
    border-radius: var(--radius-s) var(--radius-s) 0 0;
    background: color-mix(in oklab, var(--ok) 70%, transparent);
  }
  .history i.low {
    background: var(--warn);
  }
  .actions {
    display: flex;
    gap: var(--space-s);
    flex-wrap: wrap;
  }
  .rename {
    display: grid;
    gap: var(--space-s);
    padding: var(--space-m);
    border-radius: var(--radius-l);
    background: color-mix(in oklab, var(--accent-2) 10%, transparent);
    border: 1px solid color-mix(in oklab, var(--accent-2) 35%, transparent);
    font-size: var(--size-caption);
  }
  .rename input {
    padding: var(--space-s) var(--space-m);
    border: 1px solid var(--line);
    border-radius: var(--radius-m);
    background: color-mix(in oklab, var(--bg) 60%, transparent);
    color: var(--text);
    font: 600 var(--size-body) / 1.4 var(--mono);
  }
  .diff {
    display: grid;
    gap: var(--space-xxs);
    max-height: calc(5 * var(--control-l));
    overflow: auto;
    font: var(--size-caption) / var(--line-caption) var(--mono);
  }
  .diff .where {
    margin-top: var(--space-xs);
    color: var(--muted);
  }
  .del {
    color: var(--danger);
  }
  .add {
    color: var(--ok);
  }
  .uses {
    display: grid;
    gap: var(--space-xxs);
    font-size: var(--size-caption);
  }
  .uses code {
    color: var(--text);
  }
  .empty {
    color: var(--muted);
    margin: var(--space-xxl) auto;
    text-align: center;
  }
  @keyframes slide-in {
    from {
      opacity: 0;
      transform: translateX(var(--space-m));
    }
  }
</style>
