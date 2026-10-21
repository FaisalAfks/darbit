<!-- A match score coloured by verdict: ok, risky (high elsewhere too, or under the target's similarity),
     missing. -->
<script lang="ts">
  let { score, verdict }: { score: number | null; verdict: "ok" | "risky" | "missing" } = $props();
</script>

<span class="badge num" data-verdict={verdict}>{score === null ? "—" : score.toFixed(2)}</span>

<style>
  .badge {
    padding: 0 6px; border-radius: var(--radius-pill); font-size: var(--size-xs); font-weight: 700;
    color: var(--on-accent);
  }
  [data-verdict="ok"] { background: var(--ok); }
  [data-verdict="risky"] { background: var(--warn); }
  [data-verdict="missing"] { background: var(--danger); }
</style>
