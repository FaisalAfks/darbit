<!-- The live run panel, docked to a side: checkpoints, goals, steps, the current one highlighted.
     See docs/tasks/T16-player-run-panel.md. -->
<script lang="ts">
  import { on } from "$lib/api";
  import IconButton from "$lib/components/IconButton.svelte";

  interface Step { kind: string; value: unknown; note?: string; breakpoint?: boolean }
  interface Goal { name: string; steps: Step[] }
  interface Checkpoint { name: string; wait_for?: string; goals: Goal[] }
  let run: { name: string; checkpoints: Checkpoint[] } | null = $state(null);
  let at = $state({ checkpoint: 0, goal: 0, step: 0 });
  let collapsed = $state(false);

  on("run.at", (where: typeof at) => (at = where));
  // TODO(T16): run.load on open; selection; F9/F10/F5 actions; F2 edit; Insert add; ctrl+s save
</script>

<aside class="panel appear" class:collapsed>
  <header>
    <b>{run?.name ?? "No run"}</b>
    <IconButton action="run_panel.continue" label="Continue" icon="▶" />
    <IconButton action="run_panel.step" label="Step" icon="⤼" />
    <IconButton action="run_panel.stop" label="Stop" icon="■" />
    <IconButton action="view.compact" label="Collapse" icon="⇥" />
  </header>
  {#if run}
    <ol class="tree">
      {#each run.checkpoints as cp, c}
        <li class="cp" class:now={c === at.checkpoint}>◆ {cp.name}
          <ol>
            {#each cp.goals as goal, g}
              <li class="goal">{goal.name}
                <ol>
                  {#each goal.steps as step, s}
                    <li class="step num" class:now={c === at.checkpoint && g === at.goal && s === at.step} class:bp={step.breakpoint}>
                      {step.kind} {JSON.stringify(step.value)}
                    </li>
                  {/each}
                </ol>
              </li>
            {/each}
          </ol>
        </li>
      {/each}
    </ol>
  {/if}
</aside>

<style>
  .panel {
    position: fixed; top: 0; right: 0; bottom: 0; width: 300px; display: flex; flex-direction: column;
    background: var(--glass); backdrop-filter: blur(var(--blur)); border-left: 1px solid var(--line);
    transition: translate var(--move) var(--ease);
  }
  .collapsed { translate: 260px 0; }
  header { display: flex; align-items: center; gap: var(--space-1); padding: var(--space-2) var(--space-3); border-bottom: 1px solid var(--line); }
  header b { flex: 1; }
  .tree, .tree ol { list-style: none; margin: 0; padding-left: var(--space-3); }
  .tree { overflow: auto; padding: var(--space-2); font-size: var(--size-s); }
  .cp { font-weight: 600; margin-top: var(--space-2); }
  .goal { color: var(--muted); font-weight: 400; }
  .step { color: var(--text); font-size: var(--size-xs); padding: 2px 6px; border-radius: var(--radius-s); }
  .step.now { background: var(--raised-hover); box-shadow: var(--glow); }
  .step.bp::before { content: "●"; color: var(--danger); margin-right: 4px; }
</style>
