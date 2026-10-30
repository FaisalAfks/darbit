# T27 Flow editor

**Goal:** edit a flow in the Studio, as a list or a graph. Add checks, branches, loops, retries, variables and actions without code; add a Code step where the editor stops.

**Depends on:** T14, T16, T03. **Milestone:** v0.5. **Decision:** [ADR 0007](../../decisions/0007-studio-flows-and-actions.md).

## What it has

- **Two views of the same flow:** a step list (the default, compact) and a graph (for branches and loops).
- **The step palette:**
  - built-in steps: input, wait, checks, `repeat`, `retry`, `set`;
  - the bot's **functions**: sub-flows with inputs and a result;
  - its **Python actions** (`@d.action`, T29).

  All are actions with parameters, inserted the same way.
- **An inline target picker:**
  - choose from the library, with thumbnails and scores;
  - capture on the spot (T09);
  - highlight to test the picture (T11).
- **An inline condition builder:** "if `Bag.Equip` is seen within 3 s", "until `Dim.Game.Left` is gone".
- **A Code step:** call any bot function, or edit a short script inline (with syntax highlighting).
- **Functions:** select steps, then "Make a function" turns them into a named action with inputs.
- **Run controls** from the run panel (T16): run, step, breakpoints, and edits that apply live.
- **Undo and redo** for every edit; `Ctrl+S` saves.

## Files

- `packages/ui/src/apps/studio/flow/`: `FlowList.svelte`, `FlowGraph.svelte`, `StepPalette.svelte`, `ConditionBuilder.svelte`, `TargetPicker.svelte`
- `packages/darbit/src/darbit/runs/model.py`: the flow model, including functions (T14)

## Done when

A recorded flow gets two checks, a retry and a function, all in the editor, and plays back correctly.
