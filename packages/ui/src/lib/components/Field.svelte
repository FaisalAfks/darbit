<!-- A labelled form field (a setting from settings.toml): its label, the control, and help under it.
     <Field label="Speed Raid every (minutes)" help="How often to try the next character."><input type="number" /></Field> -->
<script lang="ts">
  import type { Snippet } from "svelte";

  let { label, help, children }: { label: string; help?: string; children: Snippet } = $props();
</script>

<label class="field">
  <span class="name">{label}</span>
  {@render children()}
  {#if help}<small>{help}</small>{/if}
</label>

<style>
  .field {
    display: grid;
    gap: 6px;
    min-width: 0;
    font-size: var(--size-s);
  }
  .name {
    font-weight: 600;
  }
  small {
    color: var(--slot-tool);
    font-size: var(--size-xs);
  }
  .field :global(input),
  .field :global(select),
  .field :global(textarea) {
    font: var(--size-m) / 1.3 var(--font);
    color: var(--text);
    background: var(--raised);
    border: 1px solid var(--line);
    border-radius: var(--radius-m);
    padding: 10px 12px;
    min-width: 0;
  }
</style>
