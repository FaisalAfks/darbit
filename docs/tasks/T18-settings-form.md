# T18 Settings schema and form

**Goal:** a bot declares its own settings once in `settings.toml`; darbit loads and checks the user's `config.toml` against it, and the hub shows a form for it.

**Depends on:** T03, T17. **Issue:** #51. **Milestone:** v0.5.

## The schema: `settings.toml`

```toml
[speed_raid]
label = "Speed Raid"

  [speed_raid.enabled]
  type = "bool"
  default = true
  help = "Play Speed Raid every 30 minutes."

  [speed_raid.every_minutes]
  type = "int"
  default = 30
  min = 10
  max = 120

[controls.skills]
type = "keys"                    # a key picker in the form
default = "54132"
```

Types: `bool`, `int`, `float`, `str`, `choice` (with `options`), `keys`, `target` (a target name, with a capture button), `region`, `location`, `list`.

## Files

- `src/darbit/project/settings_schema.py`: `Schema`, `load_schema()`, `load_values(schema, config_path)`, `write_values()`
- `ui/src/lib/components/Field.svelte`, `ui/src/apps/hub/SettingsForm.svelte`

## Steps

1. Load and check the schema; missing `config.toml` is created from defaults (git-ignored).
2. `load_values` returns a nested namespace like ad-bot's `cfg`, with errors naming the key and the rule.
3. The form: sections from tables, one `Field` per setting, help as `tool`-slot text under the label, a reset-to-default per field. `target`/`region`/`location` fields open the capture tool for that name (T09).
4. Saving writes `config.toml` keeping the user's comments (`tomlkit`).

## Done when

ad-bot's settings move into `settings.toml`, its `config.toml` is checked against it, and the hub edits it.

## Tests

Schema errors, value checks per type, write keeps comments.
