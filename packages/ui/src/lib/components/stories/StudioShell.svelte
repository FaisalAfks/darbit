<!-- The Studio shell from the approved mockup, built only from components, for Storybook: the top pill
     (bot switcher, sections, run controls, source and settings), the Overview or a flow, and the tools dock. -->
<script lang="ts">
  import { register } from "$lib/actions";
  import { toast } from "$lib/toasts.svelte";
  import Bar from "../Bar.svelte";
  import Button from "../Button.svelte";
  import Chip from "../Chip.svelte";
  import CommandPalette from "../CommandPalette.svelte";
  import Dock from "../Dock.svelte";
  import Field from "../Field.svelte";
  import IconButton from "../IconButton.svelte";
  import Pill from "../Pill.svelte";
  import Ring from "../Ring.svelte";
  import Segmented from "../Segmented.svelte";
  import Sheet from "../Sheet.svelte";
  import StatusList from "../StatusList.svelte";
  import StepRow from "../StepRow.svelte";
  import Tile from "../Tile.svelte";
  import Toast from "../Toast.svelte";

  let {
    view = "overview",
    sheet = "none",
    palette = false,
    showSource = false,
  }: { view?: string; sheet?: "none" | "bots" | "app"; palette?: boolean; showSource?: boolean } = $props();

  let section = $derived(view); // follows the story's controls; clicking still changes it
  let botsOpen = $derived(sheet === "bots");
  let appOpen = $derived(sheet === "app");
  let paletteOpen = $derived(palette);
  let sources = $derived(showSource);
  let chosenStep = $state("5");

  const SECTIONS = [
    { value: "overview", label: "Overview", icon: "◉" },
    { value: "flows", label: "Flows", icon: "⑂" },
    { value: "library", label: "Library", icon: "▣" },
    { value: "runs", label: "Runs", icon: "≡" },
    { value: "settings", label: "Settings", icon: "⚙" },
  ];

  const TOOLS = [
    { label: "Capture", icon: "▣", tone: "kind-image", onclick: () => toast("Capture: the screen freezes in 3 s") },
    { label: "Highlight", icon: "◎", tone: "ok", onclick: () => toast("Highlight: scanning 165 targets") },
    { label: "Record", icon: "●", tone: "danger", onclick: () => toast("Recording: Ctrl+Alt+R to stop") },
    { label: "Play", icon: "▶", tone: "accent-2" },
    { label: "Guide", icon: "☰", tone: "warn", gap: true },
    { label: "Check", icon: "✓", tone: "info" },
  ];

  register({ name: "palette.open", label: "Commands", run: () => (paletteOpen = true) });
  register({ name: "studio.overview", label: "Go to Overview", run: () => (section = "overview") });
  register({ name: "studio.flows", label: "Go to Flows", run: () => (section = "flows") });
  register({ name: "capture.freeze", label: "Capture", run: () => toast("Capture: the screen freezes in 3 s") });
  register({ name: "run.pause", label: "Pause the bot", run: () => toast("ad-bot paused", "bot", "ad-bot") });
</script>

<div class="studio">
  <header class="top">
    <div class="anchor">
      <Pill label="Bot">
        <button class="switcher" aria-expanded={botsOpen} onclick={() => (botsOpen = !botsOpen)}>
          <span class="avatar">ad</span>ad-bot<span class="caret" aria-hidden="true">▾</span>
        </button>
      </Pill>
      <Sheet title="Your bots" bind:open={botsOpen} side="left" width={620}>
        {#snippet actions()}<Button label="Install a bot" icon="＋" variant="primary" size="s" />{/snippet}
        <div class="bots">
          <article class="bot"><b>ad-bot</b><span>Speed Raid › Sakura</span><Chip text="running" tone="ok" /></article>
          <article class="bot"><b>fish-bot</b><span>idle · last run yesterday</span><Chip text="update v0.2.1" tone="info" /></article>
        </div>
      </Sheet>
    </div>
    <Segmented items={SECTIONS} bind:value={section} label="Studio sections" variant="nav" />
    <Pill label="Run controls">
      <span class="running"><span class="dot"></span><b>Running</b> 3 h 12 m</span>
      <IconButton label="Pause" icon="❚❚" action="run.pause" />
      <IconButton label="Stop" icon="■" />
    </Pill>
    <div class="anchor">
      <Pill label="Studio">
        <IconButton label="Where each tile comes from" icon="‹/›" bind:pressed={sources} />
        <IconButton label="Studio settings" icon="⚙" onclick={() => (appOpen = !appOpen)} />
      </Pill>
      <Sheet title="Studio" bind:open={appOpen} side="right" width={360}>
        <Field label="Theme"><select><option>Glass dark</option><option>Glass light</option><option>Midnight</option><option>High contrast</option></select></Field>
        <Field label="darbit" help="Each bot pins its own; this is the Studio's."><select><option>0.3.0 (latest)</option></select></Field>
      </Sheet>
    </div>
  </header>

  <main>
    {#if section === "flows"}
      <div class="flow">
        <div class="steps">
          <StepRow number="1" kind="checkpoint" text="Checkpoint Wave 1 waits for Dim.Game.Left up to 30 s" chip="0.84" selected={chosenStep === "1"} onclick={() => (chosenStep = "1")} />
          <StepRow number="2" kind="input" text="Hold W" selected={chosenStep === "2"} onclick={() => (chosenStep = "2")} />
          <StepRow number="3" kind="wait" text="Wait 0.5 s" selected={chosenStep === "3"} onclick={() => (chosenStep = "3")} />
          <StepRow number="4" kind="input" text="Release W" selected={chosenStep === "4"} onclick={() => (chosenStep = "4")} />
          <StepRow number="5" kind="loop" text="Repeat until Dim.Game.Leave shows" chip="loop" selected={chosenStep === "5"} onclick={() => (chosenStep = "5")} />
          <StepRow number="5.1" kind="call" depth={1} text="spam_skills, 5 times" chip="action" selected={chosenStep === "5.1"} onclick={() => (chosenStep = "5.1")} />
          <StepRow number="5.2" kind="check" depth={1} text="If Dim.Boss.Bar shows" selected={chosenStep === "5.2"} onclick={() => (chosenStep = "5.2")} />
          <StepRow number="5.2.1" kind="call" depth={2} text="dodge()" chip="function" selected={chosenStep === "5.2.1"} onclick={() => (chosenStep = "5.2.1")} />
          <StepRow number="6" kind="input" text="Click Dim.Game.Leave" note="back to the lobby" selected={chosenStep === "6"} onclick={() => (chosenStep = "6")} />
        </div>
        <Tile title="Step {chosenStep}" span={1}>
          <Field label="Check every"><select><option>0.5 s</option><option>1 s</option></select></Field>
          <Field label="Give up after"><select><option>never</option><option>5 min</option></select></Field>
          <Field label="Note" help="Shown in the run panel; saved as the comment on its line."><input value="fight until the end screen" /></Field>
        </Tile>
      </div>
    {:else}
      <div class="bento">
        <Tile title="Progress" span={5} showSource={sources} source={'d.progress("Speed Raid this week", state.sr_done, 133)'}>
          <div class="row">
            <Ring label="Speed Raid this week" done={32} total={133} />
            <div class="bars"><Bar label="Boss Rush today" done={1} total={1} /><Bar label="Raid Challenge today" done={0} total={1} /></div>
          </div>
        </Tile>
        <Tile title="Today's round" span={7} showSource={sources} source={'for mode in ROUND:\n    with d.step(mode.name): mode.play()'}>
          <StatusList
            label="Today's round"
            items={[
              { name: "Raid", detail: "11:02 · 41 m", status: "ok", chip: { text: "done", tone: "ok" } },
              { name: "Speed Raid", detail: "11:24 · now", status: "now", chip: { text: "running", tone: "info" } },
              { name: "Boss Rush", detail: "10:20 · 6 m", status: "ok", chip: { text: "1 / 1 today" } },
              { name: "AFK", detail: "09:12 · failed", status: "bad", chip: { text: "no rewards", tone: "danger" } },
            ]}
          />
        </Tile>
        <Tile title="Watching" span={12} showSource={sources} source={'d.observe(img.DISCONNECTED)\nd.observe(roblox_closed, name="Roblox closed")'}>
          <StatusList
            label="Watching"
            items={[
              { name: "Disconnected", detail: "fired 0 times today", status: "ok", chip: { text: "watching", tone: "ok" } },
              { name: "Roblox closed", detail: "fired once, 08:41 · rejoined", status: "ok", chip: { text: "watching", tone: "ok" } },
            ]}
          />
        </Tile>
      </div>
    {/if}
  </main>

  <div class="dock"><Dock tools={TOOLS} /></div>
  <CommandPalette bind:open={paletteOpen} />
  <Toast />
</div>

<style>
  .studio {
    position: relative;
    width: min(calc(40 * var(--space-xxxl)), 96vw);
    min-height: calc(19 * var(--control-l));
    display: grid;
    grid-template-rows: auto 1fr;
    gap: var(--space-l);
    padding: var(--space-xxl) var(--space-xxl) calc(3 * var(--control-l));
    font-size: var(--size-body);
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
    background: var(--ok);
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
    border-radius: var(--radius-xl);
    background: var(--raised);
  }
  .bot span {
    color: var(--muted);
    font-size: var(--size-caption);
  }
  .bento {
    display: grid;
    grid-template-columns: repeat(12, 1fr);
    gap: var(--space-l);
    align-content: start;
  }
  .row {
    display: grid;
    grid-template-columns: auto 1fr;
    gap: var(--space-xxl);
    align-items: center;
  }
  .bars {
    display: grid;
    gap: var(--space-m);
  }
  .flow {
    display: grid;
    grid-template-columns: 1fr var(--width-inspector);
    gap: var(--space-xxl);
    align-items: start;
  }
  .steps {
    display: grid;
    gap: var(--space-s-nudge);
  }
  .dock {
    position: absolute;
    left: 50%;
    bottom: var(--space-xxl);
    translate: -50% 0;
    z-index: 5;
  }
</style>
