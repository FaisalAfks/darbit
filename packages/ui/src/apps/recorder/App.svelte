<!-- The recorder bar (decision 0013, round 8): a pill at the top with the time, the action's name, its steps and
     checks, Pause, Add check, the live steps and Stop. While paused, the check menu adds a wait or a picture
     check at that moment. The live steps panel lists what's been caught, newest last. -->
<script lang="ts">
  import { on, request } from "$lib/api";

  interface Shown {
    kind: string;
    text: string;
    note: string;
  }
  interface Status {
    recording: boolean;
    name?: string;
    path?: string;
    seconds?: number;
    paused?: boolean;
    count?: number;
    checks?: number;
    steps?: Shown[];
  }

  let status: Status = $state({ recording: true });
  let menu = $state(false);
  let live = $state(false);
  let pictures: string[] = $state([]);
  let target = $state("");
  let gone = $state(false);
  let timeout = $state(30);
  let wait = $state(1);
  let problem = $state("");

  const clock = $derived(clockOf(status.seconds ?? 0));

  function clockOf(seconds: number): string {
    const whole = Math.floor(seconds);
    return `${String(Math.floor(whole / 60)).padStart(2, "0")}:${String(whole % 60).padStart(2, "0")}`;
  }

  function size(): void {
    request("record.size", { open: menu || live }).catch(() => {});
  }

  async function togglePause(): Promise<void> {
    status = await request("record.pause");
    if (!status.paused) menu = false;
    size();
  }

  async function openChecks(): Promise<void> {
    if (!status.paused) status = await request("record.pause");
    menu = !menu;
    if (menu && !pictures.length && status.path) {
      const assets = await request("library.list", { path: status.path }).catch(() => []);
      pictures = assets.filter((asset: { kind: string; missing: boolean }) => asset.kind === "image" && !asset.missing).map((asset: { name: string }) => asset.name);
      target = pictures[0] ?? "";
    }
    size();
  }

  async function addWait(): Promise<void> {
    status = await request("record.check", { kind: "wait", seconds: wait });
  }

  async function addPicture(): Promise<void> {
    problem = "";
    try {
      status = await request("record.check", { kind: "picture", target, gone, timeout });
    } catch (error) {
      problem = (error as Error).message;
    }
  }

  function toggleLive(): void {
    live = !live;
    size();
  }

  $effect(() => {
    request("record.status").then((found: Status) => (status = found)).catch(() => {});
    return on("record.tick", (data: Status) => {
      if (data.recording) status = data;
    });
  });
</script>

<div class="wrap">
  <div class="pill" class:paused={status.paused}>
    <span class="rec" aria-hidden="true"></span>
    <span class="time">{clock}</span>
    <b class="name">{status.name ?? "…"}</b>
    <small>{status.count ?? 0} steps · {status.checks ?? 0} checks{status.paused ? " · paused" : ""}</small>
    <span class="sep"></span>
    <button class="check" class:on={menu} onclick={openChecks} title="Pause and add a check here">＋ Check</button>
    <button class="icon" class:on={live} aria-label="Live steps" title="Live steps" onclick={toggleLive}>≡</button>
    <button class="icon" aria-label="Forget the last step" title="Forget the last step" onclick={() => request("record.undo").then((found) => (status = found))}>↶</button>
    <button class="icon go" aria-label={status.paused ? "Go on" : "Pause"} title="{status.paused ? 'Go on' : 'Pause'} (Ctrl+Alt+P)" onclick={togglePause}>{status.paused ? "▶" : "❚❚"}</button>
    <button class="icon stop" aria-label="Stop and save" title="Stop and save (Ctrl+Alt+R)" onclick={() => request("record.stop", { keep: true })}>■</button>
  </div>

  {#if menu}
    <div class="panel">
      <h6>Paused at {clock}. Add a check here:</h6>
      <div class="option">
        <span class="ic" data-kind="image">▣</span>
        <span class="text"><b>Picture</b><small>wait for it to show, or until it's gone</small></span>
      </div>
      <div class="form">
        <select bind:value={target} aria-label="Picture">
          {#each pictures as name (name)}<option>{name}</option>{:else}<option value="">No pictures yet</option>{/each}
        </select>
        <label><input type="checkbox" bind:checked={gone} /> until gone</label>
        <label>up to <input type="number" min="1" bind:value={timeout} /> s</label>
        <button class="add" onclick={addPicture} disabled={!target}>Add</button>
      </div>
      {#if problem}<p class="bad">{problem}</p>{/if}
      <div class="option">
        <span class="ic" data-kind="wait">⏱</span>
        <span class="text"><b>Wait</b><small>a fixed pause</small></span>
      </div>
      <div class="form">
        <label><input type="number" min="0.1" step="0.1" bind:value={wait} /> s</label>
        <button class="add" onclick={addWait}>Add</button>
      </div>
      <div class="option off">
        <span class="ic">◉</span>
        <span class="text"><b>Colour at a point · area changes · text</b><small>later</small></span>
      </div>
    </div>
  {:else if live}
    <div class="panel steps">
      <h6>Caught so far, newest last</h6>
      {#each status.steps ?? [] as step, index (index)}
        <div class="step" data-kind={step.kind}><span class="n">{(status.count ?? 0) - (status.steps?.length ?? 0) + index + 1}</span><code>{step.text}</code>{#if step.note}<small>{step.note}</small>{/if}</div>
      {:else}
        <p class="muted">Nothing yet. Play: keys and clicks show up here.</p>
      {/each}
    </div>
  {/if}
</div>

<style>
  :global(html),
  :global(body) {
    margin: 0;
    background: transparent;
    overflow: hidden;
  }
  .wrap {
    display: grid;
    justify-items: center;
    gap: var(--space-s);
    padding-top: var(--space-xs);
    font-family: var(--font);
    color: var(--text);
  }
  .pill {
    display: flex;
    align-items: center;
    gap: var(--space-s);
    padding: var(--space-s) var(--space-s) var(--space-s) var(--space-l);
    border-radius: var(--radius-pill);
    background: var(--glass-strong);
    border: 1px solid var(--line);
    box-shadow: var(--shadow);
    white-space: nowrap;
    animation: drop var(--duration-normal) var(--curve-decelerate);
  }
  .rec {
    width: var(--space-m-nudge);
    height: var(--space-m-nudge);
    border-radius: 50%;
    background: var(--danger);
    animation: rec 1.4s ease-out infinite;
  }
  .paused .rec {
    background: var(--warn);
    animation: none;
  }
  @keyframes rec {
    70% {
      box-shadow: 0 0 0 var(--space-s) color-mix(in oklab, var(--danger) 0%, transparent);
    }
    0% {
      box-shadow: 0 0 0 0 color-mix(in oklab, var(--danger) 60%, transparent);
    }
  }
  .time {
    font: 700 var(--size-body) / 1 var(--mono);
  }
  .name {
    font: 700 var(--size-body) / 1 var(--font-strong);
  }
  small {
    color: var(--muted);
    font-size: var(--size-caption);
  }
  .sep {
    width: 1px;
    height: var(--space-xl);
    background: var(--line);
  }
  .check {
    height: var(--control-m);
    padding: 0 var(--space-m);
    border: 1px solid color-mix(in oklab, var(--accent) 40%, transparent);
    border-radius: var(--radius-pill);
    background: color-mix(in oklab, var(--accent) 16%, transparent);
    color: var(--accent);
    font: 700 var(--size-caption) / 1 var(--font-strong);
    cursor: pointer;
  }
  .check.on {
    background: var(--accent);
    color: var(--on-accent);
  }
  .icon {
    width: var(--control-m);
    height: var(--control-m);
    border: 0;
    border-radius: 50%;
    background: var(--raised);
    color: var(--text);
    font-size: var(--size-caption);
    cursor: pointer;
  }
  .icon.on {
    background: var(--raised-hover);
    color: var(--accent);
  }
  .icon.go {
    background: var(--accent);
    color: var(--on-accent);
  }
  .icon.stop {
    background: color-mix(in oklab, var(--danger) 20%, transparent);
    color: var(--danger);
  }
  .panel {
    width: calc(100% - 2 * var(--space-l));
    box-sizing: border-box;
    display: grid;
    gap: var(--space-s);
    padding: var(--space-m);
    border-radius: var(--radius-xl);
    background: var(--glass-strong);
    border: 1px solid var(--line);
    box-shadow: var(--shadow);
    animation: drop var(--duration-normal) var(--curve-decelerate);
  }
  h6 {
    margin: 0 var(--space-xs) var(--space-xs);
    font: 600 var(--size-caption) / 1.3 var(--font);
    color: var(--muted);
  }
  .option {
    display: flex;
    align-items: center;
    gap: var(--space-m);
  }
  .option.off {
    opacity: 0.45;
  }
  .ic {
    width: var(--control-l);
    height: var(--control-l);
    display: grid;
    place-items: center;
    border-radius: var(--radius-m);
    background: var(--raised);
    color: var(--muted);
  }
  .ic[data-kind="image"] {
    color: var(--kind-image);
    background: color-mix(in oklab, var(--kind-image) 18%, transparent);
  }
  .ic[data-kind="wait"] {
    color: var(--warn);
    background: color-mix(in oklab, var(--warn) 18%, transparent);
  }
  .text {
    display: grid;
  }
  .form {
    display: flex;
    align-items: center;
    gap: var(--space-s);
    margin: 0 0 var(--space-s) calc(var(--control-l) + var(--space-m));
    font-size: var(--size-caption);
    flex-wrap: wrap;
  }
  .form select,
  .form input[type="number"] {
    padding: var(--space-xs) var(--space-s);
    border: 1px solid var(--line);
    border-radius: var(--radius-m);
    background: var(--raised);
    color: var(--text);
    font: inherit;
  }
  .form input[type="number"] {
    width: calc(2 * var(--control-m));
  }
  .add {
    height: var(--control-s);
    padding: 0 var(--space-m);
    border: 0;
    border-radius: var(--radius-pill);
    background: var(--accent);
    color: var(--on-accent);
    font: 700 var(--size-caption) / 1 var(--font-strong);
    cursor: pointer;
  }
  .add:disabled {
    opacity: 0.4;
  }
  .steps {
    max-height: calc(9 * var(--control-l));
    overflow: auto;
  }
  .step {
    display: grid;
    grid-template-columns: var(--control-m) 1fr auto;
    gap: var(--space-s);
    align-items: center;
    padding: var(--space-xs) var(--space-s);
    border-radius: var(--radius-m);
    animation: drop var(--duration-normal) var(--curve-decelerate);
  }
  .step:last-child {
    background: color-mix(in oklab, var(--danger) 12%, transparent);
  }
  .step[data-kind="check"] {
    background: color-mix(in oklab, var(--accent) 10%, transparent);
    box-shadow: inset 2px 0 0 var(--accent);
  }
  .step .n {
    color: var(--faint);
    font: 600 var(--size-caption) / 1 var(--mono);
  }
  .step code {
    font: var(--size-caption) / 1.4 var(--mono);
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }
  .muted {
    color: var(--muted);
    font-size: var(--size-caption);
    margin: var(--space-s);
  }
  .bad {
    color: var(--danger);
    font-size: var(--size-caption);
    margin: 0;
  }
  @keyframes drop {
    from {
      opacity: 0;
      transform: translateY(calc(-1 * var(--space-s)));
    }
  }
</style>
