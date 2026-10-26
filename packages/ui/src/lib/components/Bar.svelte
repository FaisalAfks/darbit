<!-- A labelled progress bar: "Boss Rush today  1 / 1". Full bars turn green. -->
<script lang="ts">
  let { label, done, total }: { label: string; done: number; total: number } = $props();

  const share = $derived(total > 0 ? Math.min(1, Math.max(0, done / total)) : 0);
</script>

<div class="bar">
  <span class="line"><b>{label}</b><span class="num">{done} / {total}</span></span>
  <span
    class="track"
    class:full={share === 1}
    role="progressbar"
    aria-label={label}
    aria-valuenow={done}
    aria-valuemin={0}
    aria-valuemax={total}
  >
    <i style:transform="scaleX({share})"></i>
  </span>
</div>

<style>
  .bar {
    display: grid;
    gap: var(--space-2);
    font-size: var(--size-s);
  }
  .line {
    display: flex;
    justify-content: space-between;
    gap: var(--space-3);
  }
  b {
    font-weight: 600;
  }
  .num {
    font-family: var(--mono);
    color: var(--muted);
  }
  .track {
    display: block;
    height: 8px;
    border-radius: var(--radius-pill);
    background: var(--raised);
    overflow: hidden;
  }
  i {
    display: block;
    height: 100%;
    transform-origin: left;
    background: var(--accent);
    transition: transform var(--move) var(--ease);
  }
  .full i {
    background: var(--ok);
  }
</style>
