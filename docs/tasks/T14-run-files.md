# T14 Run file format

> **Redefined 2026-10-25** ([ADR 0007](../decisions/0007-studio-flows-and-actions.md)): run files are **flows**. The same model also holds checks (`wait_for`, `if`/`else`, `until`, `retry`, `on_fail`), `repeat`, `set`, calls, and functions (`define`, `call`, `return`), so the recorder, the player, the flow editor (T27) and export (T28) share it.

**Goal:** the YAML format for recorded runs, its model in Python, and a JSON Schema so editors check and complete it.

**Depends on:** nothing. **Issue:** #49. **Milestone:** v0.4. **Design:** [design.md §8](../design.md).

## The format

```yaml
run: Slime                      # name
darbit: 0.4                     # format version
window: Roblox                  # the app it's played in; positions are relative to this window
checkpoints:
  - name: Wave 1
    wait_for: Dim.Game.Left     # a target that must be on screen before this part starts (timeout: 30)
    timeout: 30
    goals:
      - name: Clear the left side
        steps:
          - hold: w             # key down
          - wait: 0.5
          - release: w
          - press: q            # down and up
          - do: dodge           # an action below
          - turn: -90           # camera, degrees (right-drag or arrow keys, as recorded)
          - click: [0.42, 0.61] # a click, as a fraction of the window
          - until: Dim.Game.Next  # wait for a target, as a step
actions:
  dodge: [press: space, wait: 0.3, press: space]
```

Step kinds: `press`, `hold`, `release`, `write`, `wait`, `click`, `right_click`, `move`, `drag`, `scroll`, `turn`, `until`, `do`. Each may have `note:` (shown in the run panel) and `break: true` (a saved breakpoint).

## Files

- `packages/darbit/src/darbit/runs/model.py`: dataclasses `Run`, `Checkpoint`, `Goal`, `Step`; `load(path)`, `dump(run)`
- `packages/darbit/src/darbit/runs/runfile.schema.json`: generated from the model (`python -m darbit.runs.model --schema`)
- `pyproject.toml`: `pyyaml` in the `runs` part of the dependencies (small; add to the main list)

## Steps

1. Model with plain dataclasses; `Step` is `kind`, `value`, `note`, `breakpoint`. Positions in `click`/`move`/`drag` are fractions of the window (so a run plays at any window size, as T22's targets do).
2. `load` checks: unknown step kinds, `do:` naming a missing action, actions calling themselves → errors with the YAML line (`yaml.compose` keeps line numbers).
3. `dump` writes the same layout back (flow style for short step lists, comments kept where possible with `ruamel.yaml` if it's worth the dependency; otherwise document that comments are lost).
4. Schema: JSON Schema draft 2020-12, with descriptions, so VS Code's YAML extension shows help. Add a `# yaml-language-server: $schema=` line in files the recorder writes.

## Done when

The example above loads, dumps to the same file, validates with the schema, and errors point at the right line.

## Tests

Round trip, every error, the schema validates the example and rejects a broken one (`jsonschema` in dev dependencies).
