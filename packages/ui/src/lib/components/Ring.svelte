<!-- A progress ring for d.progress(label, done, total): "32 of 133", the label under it. -->
<script lang="ts">
  let { label, done, total, size = 120 }: { label: string; done: number; total: number; size?: number } = $props();

  const share = $derived(total > 0 ? Math.min(1, Math.max(0, done / total)) : 0);
</script>

<figure class="ring-box">
  <div
    class="ring"
    style:--share="{share * 100}%"
    style:--size="{size}px"
    role="progressbar"
    aria-label={label}
    aria-valuenow={done}
    aria-valuemin={0}
    aria-valuemax={total}
  >
    <div><b>{done}</b><span>of {total}</span></div>
  </div>
  <figcaption>{label}</figcaption>
</figure>

<style>
  .ring-box {
    margin: 0;
    display: grid;
    justify-items: center;
    gap: var(--space-2);
  }
  .ring {
    width: var(--size);
    height: var(--size);
    display: grid;
    place-items: center;
    text-align: center;
    border-radius: 50%;
    background:
      radial-gradient(closest-side, var(--glass-strong) 78%, transparent 79%),
      conic-gradient(var(--accent) var(--share), var(--raised) 0);
  }
  b {
    display: block;
    font: 700 var(--size-xl) / 1.1 var(--font-strong);
  }
  span {
    font-size: var(--size-xs);
    color: var(--muted);
  }
  figcaption {
    font-size: var(--size-s);
    color: var(--muted);
    text-align: center;
  }
</style>
