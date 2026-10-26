<!-- One step of a flow (decision 0010): its number, an icon in its kind's colour, what it does, and an optional
     chip and note (the comment on its line). Nested steps are indented by `depth`. Click selects it.
     <StepRow number="5" kind="loop" text="Repeat until Dim.Game.Leave shows" chip="loop" selected /> -->
<script lang="ts">
  import type { Snippet } from "svelte";

  export type Kind = "input" | "wait" | "check" | "loop" | "call" | "code" | "checkpoint";

  const ICONS: Record<Kind, string> = {
    input: "⌨",
    wait: "⏱",
    check: "⑂",
    loop: "↻",
    call: "ƒ",
    code: "{ }",
    checkpoint: "◆",
  };

  let {
    number,
    kind,
    text,
    depth = 0,
    chip,
    note,
    selected = false,
    onclick,
    children,
  }: {
    number: string;
    kind: Kind;
    text?: string;
    depth?: number;
    chip?: string;
    note?: string;
    selected?: boolean;
    onclick?: () => void;
    children?: Snippet; // instead of `text`, for steps with values and targets in them
  } = $props();
</script>

<button class="step" data-kind={kind} style:--depth={depth} aria-current={selected ? "step" : undefined} {onclick}>
  <span class="number">{number}</span>
  <span class="icon" aria-hidden="true">{ICONS[kind]}</span>
  <span class="text">{#if children}{@render children()}{:else}{text}{/if}</span>
  {#if note}<span class="note"># {note}</span>{/if}
  {#if chip}<span class="chip">{chip}</span>{/if}
</button>

<style>
  .step {
    --k: var(--muted);
    width: calc(100% - var(--depth) * 46px);
    margin-left: calc(var(--depth) * 46px);
    min-height: 54px;
    display: grid;
    grid-template-columns: 40px 34px 1fr auto auto;
    gap: var(--space-3);
    align-items: center;
    padding: var(--space-2) 14px var(--space-2) 10px;
    border: 1px solid transparent;
    border-radius: 14px;
    background: var(--raised);
    color: var(--text);
    font: var(--size-m) / 1.3 var(--font);
    text-align: left;
    cursor: pointer;
    transition: background var(--fast) var(--ease);
  }
  .step:hover {
    background: var(--raised-hover);
  }
  [aria-current="step"] {
    border-color: var(--accent);
    background: color-mix(in oklab, var(--accent) 10%, var(--raised));
  }
  [data-kind="check"] {
    --k: var(--kind-image);
  }
  [data-kind="loop"] {
    --k: var(--info);
  }
  [data-kind="call"] {
    --k: var(--accent-2);
  }
  [data-kind="code"] {
    --k: var(--warn);
  }
  [data-kind="checkpoint"] {
    --k: var(--ok);
  }
  .number {
    font: 600 var(--size-xs) / 1 var(--mono);
    color: var(--faint);
    text-align: right;
  }
  .icon {
    width: 34px;
    height: 34px;
    display: grid;
    place-items: center;
    border-radius: 10px;
    font-size: var(--size-m);
    color: var(--k);
    background: color-mix(in oklab, var(--k) 16%, transparent);
  }
  .text {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: var(--space-2);
    min-width: 0;
  }
  .note {
    color: var(--faint);
    font-size: var(--size-s);
  }
  .chip {
    padding: 2px 10px;
    border-radius: var(--radius-pill);
    font: 600 var(--size-xs) / 1.6 var(--font-strong);
    color: var(--k);
    background: color-mix(in oklab, var(--k) 14%, transparent);
    border: 1px solid color-mix(in oklab, var(--k) 32%, transparent);
  }
  @media (max-width: 760px) {
    .step {
      grid-template-columns: 34px 1fr auto;
      width: calc(100% - var(--depth) * 16px);
      margin-left: calc(var(--depth) * 16px);
    }
    .number,
    .note {
      display: none;
    }
  }
</style>
