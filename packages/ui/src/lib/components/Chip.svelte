<!-- A small label: a kind, a status, a version. <Chip text="running" tone="ok" /> -->
<script lang="ts">
  export type Tone = "neutral" | "accent" | "image" | "region" | "point" | "ok" | "warn" | "danger" | "info";

  let { text, tone = "neutral", icon }: { text: string; tone?: Tone; icon?: string } = $props();
</script>

<span class="chip" data-tone={tone}>{#if icon}<span aria-hidden="true">{icon}</span>{/if}{text}</span>

<style>
  .chip {
    --c: var(--muted);
    display: inline-flex;
    align-items: center;
    gap: var(--space-1);
    padding: 2px 10px;
    border-radius: var(--radius-pill);
    font: 600 var(--size-xs) / 1.6 var(--font-strong);
    white-space: nowrap;
    color: var(--c);
    background: color-mix(in oklab, var(--c) 14%, transparent);
    border: 1px solid color-mix(in oklab, var(--c) 32%, transparent);
  }
  [data-tone="accent"] {
    --c: var(--accent);
  }
  [data-tone="image"] {
    --c: var(--kind-image);
  }
  [data-tone="region"] {
    --c: var(--kind-region);
  }
  [data-tone="point"] {
    --c: var(--kind-point);
  }
  [data-tone="ok"] {
    --c: var(--ok);
  }
  [data-tone="warn"] {
    --c: var(--warn);
  }
  [data-tone="danger"] {
    --c: var(--danger);
  }
  [data-tone="info"] {
    --c: var(--info);
  }
</style>
