<!-- The Studio Overview from the approved mockup, built only from components, for Storybook. -->
<script lang="ts">
  import Bar from "../Bar.svelte";
  import Button from "../Button.svelte";
  import Chip from "../Chip.svelte";
  import Field from "../Field.svelte";
  import Ring from "../Ring.svelte";
  import Switch from "../Switch.svelte";
  import Tile from "../Tile.svelte";

  let { showSource = false }: { showSource?: boolean } = $props();
  let speedRaid = $state(true);
  let afk = $state(false);
</script>

<div class="grid">
  <Tile title="Progress" span={5} {showSource} source={'d.progress("Speed Raid this week", state.sr_done, 133)\nd.progress("Boss Rush today", used, 1)'}>
    <div class="row">
      <Ring label="Speed Raid this week" done={32} total={133} />
      <div class="bars">
        <Bar label="Boss Rush today" done={1} total={1} />
        <Bar label="Raid Challenge today" done={0} total={1} />
      </div>
    </div>
  </Tile>
  <Tile title="Watching" span={7} {showSource} source={'d.observe(img.DISCONNECTED, region=cfg.region.main_menu)\nd.observe(roblox_closed, name="Roblox closed")'}>
    {#snippet extra()}<Chip text="2 observers" />{/snippet}
    <ul>
      <li><b>Disconnected</b><span>fired 0 times today</span><Chip text="watching" tone="ok" /></li>
      <li><b>Roblox closed</b><span>fired once, 08:41 · rejoined</span><Chip text="watching" tone="ok" /></li>
    </ul>
  </Tile>
  <Tile title="Modes" span={6} {showSource} source={'[speed_raid.enabled]      # settings.toml\ntype = "bool"\ndefault = true'}>
    <Switch label="Speed Raid" help="The next character, every 30 minutes." bind:checked={speedRaid} />
    <Switch label="AFK" help="Claim the AFK rewards." bind:checked={afk} />
  </Tile>
  <Tile title="Speed Raid" span={6}>
    <Field label="Speed Raid every (minutes)" help="How often to try the next character."><input type="number" value="30" /></Field>
    <div class="actions"><Button label="Restore defaults" variant="quiet" /><Button label="Save" variant="primary" /></div>
  </Tile>
</div>

<style>
  .grid {
    display: grid;
    grid-template-columns: repeat(12, 1fr);
    gap: var(--space-l);
    width: min(calc(34 * var(--space-xxxl)), 92vw);
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
  ul {
    list-style: none;
    margin: 0;
    padding: 0;
    display: grid;
    gap: var(--space-xs);
  }
  li {
    display: grid;
    grid-template-columns: 1fr auto auto;
    gap: var(--space-m);
    align-items: center;
    padding: var(--space-s) var(--space-m);
    border-radius: var(--radius-m);
  }
  li span {
    color: var(--muted);
    font-size: var(--size-caption);
  }
  .actions {
    display: flex;
    justify-content: flex-end;
    gap: var(--space-s);
  }
</style>
