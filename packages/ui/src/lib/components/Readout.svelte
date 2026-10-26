<!-- Where and how big, for every kind: image "w × h", region "x, y · w × h", point "x, y".
     Click it to type exact numbers; Enter applies (onchange), Esc cancels. -->
<script lang="ts">
  export interface Value {
    x: number;
    y: number;
    w?: number;
    h?: number;
  }

  let {
    x,
    y,
    w,
    h,
    kind,
    onchange,
  }: Value & { kind: "image" | "region" | "point"; onchange?: (value: Value) => void } = $props();

  let editing = $state(false);
  let draft = $state<Value>({ x: 0, y: 0 });
  let form: HTMLElement | undefined = $state();

  const hasSize = $derived(w !== undefined && h !== undefined);
  const text = $derived(describe(kind, x, y, w, h));

  function describe(which: string, left: number, top: number, width?: number, height?: number): string {
    if (width === undefined || height === undefined) return `${left}, ${top}`;
    if (which === "image") return `${width} × ${height}`;
    return `${left}, ${top} · ${width} × ${height}`;
  }

  function edit(): void {
    draft = { x, y, w, h };
    editing = true;
    queueMicrotask(() => form?.querySelector("input")?.select());
  }

  function onkeydown(event: KeyboardEvent): void {
    if (event.key === "Enter") {
      editing = false;
      onchange?.({ ...draft });
    } else if (event.key === "Escape") {
      editing = false;
    } else {
      return;
    }
    event.preventDefault();
  }
</script>

{#if editing}
  <span bind:this={form} class="readout editing" data-kind={kind} role="group" aria-label="Exact position">
    <input type="number" bind:value={draft.x} aria-label="x" {onkeydown} />,
    <input type="number" bind:value={draft.y} aria-label="y" {onkeydown} />
    {#if hasSize}
      ·
      <input type="number" bind:value={draft.w} aria-label="width" min="1" {onkeydown} /> ×
      <input type="number" bind:value={draft.h} aria-label="height" min="1" {onkeydown} />
    {/if}
  </span>
{:else}
  <button class="readout" data-kind={kind} onclick={edit} title="Click to type exact pixels">{text}</button>
{/if}

<style>
  .readout {
    --k: var(--accent);
    display: inline-flex;
    align-items: center;
    gap: var(--space-xxs);
    min-height: var(--control-s); /* WCAG 2.2: 24 px targets */
    padding: var(--space-xxs) var(--space-s);
    border: 0;
    border-radius: var(--radius-s);
    font: 600 var(--size-caption) / 1.5 var(--mono);
    color: var(--on-accent);
    background: var(--k);
    white-space: nowrap;
    cursor: text;
  }
  [data-kind="image"] {
    --k: var(--kind-image);
  }
  [data-kind="region"] {
    --k: var(--kind-region);
  }
  [data-kind="point"] {
    --k: var(--kind-point);
  }
  input {
    width: calc(7 * var(--space-s));
    padding: 0 var(--space-xs);
    border: 0;
    border-radius: var(--radius-s);
    font: inherit;
    color: var(--text);
    background: var(--glass-strong);
  }
</style>
