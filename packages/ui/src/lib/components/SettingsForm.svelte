<!-- A bot's settings page, made from its settings.toml (server: project/settings_schema.as_json): a tile per
     section, a control per setting by its type, help under each, and "Restore default" when it differs.
     <SettingsForm sections={schema} bind:values onsave={save} /> -->
<script lang="ts">
  import Button from "./Button.svelte";
  import Field from "./Field.svelte";
  import Keycap from "./Keycap.svelte";
  import Readout from "./Readout.svelte";
  import Switch from "./Switch.svelte";
  import Tile from "./Tile.svelte";

  export interface Setting {
    key: string;
    type: "bool" | "int" | "float" | "str" | "choice" | "keys" | "target" | "region" | "location" | "list";
    default: unknown;
    label: string;
    help: string;
    rules: { min?: number; max?: number; options?: string[] };
  }

  export interface Section {
    key: string;
    label: string;
    help: string;
    settings: Setting[];
  }

  let {
    sections,
    values = $bindable({}),
    onsave,
    showSource = false,
  }: {
    sections: Section[];
    values?: Record<string, unknown>; // flat: {"speed_raid.enabled": true}
    onsave?: (values: Record<string, unknown>) => void;
    showSource?: boolean;
  } = $props();

  function value(setting: Setting): unknown {
    return setting.key in values ? values[setting.key] : setting.default;
  }

  function change(setting: Setting, next: unknown): void {
    values = { ...values, [setting.key]: next };
  }

  function changed(setting: Setting): boolean {
    return JSON.stringify(value(setting)) !== JSON.stringify(setting.default);
  }

  function source(section: Section): string {
    const lines: string[] = [];
    for (const setting of section.settings.slice(0, 1)) {
      lines.push(`[${setting.key}]      # settings.toml`, `type = "${setting.type}"`, `default = ${JSON.stringify(setting.default)}`);
    }
    return lines.join("\n");
  }

  function numbers(setting: Setting): number[] {
    const current = value(setting);
    return Array.isArray(current) ? (current as number[]) : [0, 0, 0, 0];
  }
</script>

<div class="form">
  {#each sections as section (section.key)}
    <Tile title={section.label || "Settings"} span={6} {showSource} source={source(section)}>
      {#if section.help}<p class="help">{section.help}</p>{/if}
      {#each section.settings as setting (setting.key)}
        <div class="setting">
          {#if setting.type === "bool"}
            <Switch label={setting.label} help={setting.help} checked={value(setting) === true} onchange={(on) => change(setting, on)} />
          {:else if setting.type === "int" || setting.type === "float"}
            <Field label={setting.label} help={setting.help}>
              <input
                type="number"
                value={value(setting)}
                min={setting.rules.min}
                max={setting.rules.max}
                step={setting.type === "int" ? 1 : "any"}
                oninput={(event) => change(setting, Number(event.currentTarget.value))}
              />
            </Field>
          {:else if setting.type === "choice"}
            <Field label={setting.label} help={setting.help}>
              <select value={value(setting)} onchange={(event) => change(setting, event.currentTarget.value)}>
                {#each setting.rules.options ?? [] as option (option)}<option>{option}</option>{/each}
              </select>
            </Field>
          {:else if setting.type === "keys"}
            <Field label={setting.label} help={setting.help}>
              <span class="keys">
                {#each String(value(setting)).split("") as key, index (index)}<Keycap keys={key} />{/each}
                <Button label="Record keys" size="s" />
              </span>
            </Field>
          {:else if setting.type === "region" || setting.type === "location"}
            {@const [x, y, w, h] = numbers(setting)}
            <Field label={setting.label} help={setting.help}>
              <span class="keys">
                {#if setting.type === "region"}<Readout kind="region" {x} {y} {w} {h} />{:else}<Readout kind="point" {x} {y} />{/if}
                <Button label="Capture" icon="▣" size="s" />
              </span>
            </Field>
          {:else}
            <Field label={setting.label} help={setting.help}>
              <input value={String(value(setting) ?? "")} oninput={(event) => change(setting, event.currentTarget.value)} />
            </Field>
          {/if}
          {#if changed(setting)}
            <Button label="Restore default" variant="quiet" size="s" onclick={() => change(setting, setting.default)} />
          {/if}
        </div>
      {/each}
    </Tile>
  {/each}
</div>
{#if onsave}
  <div class="actions"><Button label="Save" variant="primary" onclick={() => onsave?.(values)} /></div>
{/if}

<style>
  .form {
    display: grid;
    grid-template-columns: repeat(12, 1fr);
    gap: var(--space-l);
    align-items: start;
  }
  .setting {
    display: grid;
    gap: var(--space-xs);
    justify-items: start;
  }
  .setting > :global(*:first-child) {
    justify-self: stretch;
  }
  .help {
    margin: 0;
    color: var(--muted);
    font-size: var(--size-body);
  }
  .keys {
    display: flex;
    align-items: center;
    gap: var(--space-xs);
    flex-wrap: wrap;
  }
  .actions {
    display: flex;
    justify-content: flex-end;
    margin-top: var(--space-l);
  }
  @media (max-width: 760px) {
    .form :global(.tile) {
      grid-column: 1 / -1;
    }
  }
</style>
