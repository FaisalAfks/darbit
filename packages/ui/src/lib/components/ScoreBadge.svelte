<!-- A match score coloured by its verdict. Without a verdict it's worked out from the score:
     ok at 0.9 and up (and at least the target's similarity), risky from the similarity, missing below it.
     <ScoreBadge score={0.88} similarity={0.85} />   <ScoreBadge score={null} /> -->
<script lang="ts">
  type Verdict = "ok" | "risky" | "missing";

  let {
    score,
    similarity = 0.85,
    verdict,
    note,
  }: { score: number | null; similarity?: number; verdict?: Verdict; note?: string } = $props();

  function judge(value: number | null, needed: number): Verdict {
    if (value === null || value < needed) return "missing";
    if (value >= 0.9) return "ok";
    return "risky";
  }

  const shown = $derived(verdict ?? judge(score, similarity));
  const text = $derived(score === null ? "—" : score.toFixed(2));
</script>

<span class="badge" data-verdict={shown}>{text}{#if note}<span class="note">{note}</span>{/if}</span>

<style>
  .badge {
    display: inline-flex;
    gap: var(--space-xs);
    align-items: baseline;
    padding: 0 var(--space-s);
    border-radius: var(--radius-pill);
    font: 700 var(--size-caption) / 1.6 var(--mono);
    color: var(--on-status);
  }
  [data-verdict="ok"] {
    background: var(--ok);
  }
  [data-verdict="risky"] {
    background: var(--warn);
  }
  [data-verdict="missing"] {
    background: var(--danger);
  }
  .note {
    font-family: var(--font);
    font-weight: 600;
  }
</style>
