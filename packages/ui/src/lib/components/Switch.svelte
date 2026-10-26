<!-- An on/off setting, with its name and help beside it (a bool in settings.toml).
     <Switch label="Speed Raid" help="The next character, every 30 minutes." bind:checked /> -->
<script lang="ts">
  let { label, help, checked = $bindable(false) }: { label: string; help?: string; checked?: boolean } = $props();
</script>

<label class="row">
  <span class="text"><b>{label}</b>{#if help}<small>{help}</small>{/if}</span>
  <button class="switch" role="switch" aria-checked={checked} aria-label={label} onclick={() => (checked = !checked)}></button>
</label>

<style>
  .row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: var(--space-l);
    padding: var(--space-m) var(--space-l);
    border-radius: var(--radius-m);
    background: var(--raised);
    cursor: pointer;
  }
  .text {
    display: grid;
    gap: 2px;
    min-width: 0;
  }
  b {
    font: 600 var(--size-content) / var(--line-content) var(--font-strong);
  }
  small {
    color: var(--muted);
    font-size: var(--size-caption);
  }
  .switch {
    position: relative;
    flex: none;
    --track-width: 44px; /* a thumb and its travel */
    --thumb: var(--space-xl);
    width: var(--track-width);
    height: calc(var(--thumb) + 2 * var(--space-xxs) + 2px);
    border: 1px solid var(--line);
    border-radius: var(--radius-pill);
    background: var(--raised);
    cursor: pointer;
    transition: background var(--duration-fast) var(--curve-easy-ease);
  }
  .switch::after {
    content: "";
    position: absolute;
    top: 2px;
    left: 2px;
    width: var(--thumb);
    height: var(--thumb);
    border-radius: 50%;
    background: var(--muted);
    transition: transform var(--duration-fast) var(--curve-easy-ease);
  }
  [aria-checked="true"] {
    background: var(--accent);
    border-color: var(--accent);
  }
  [aria-checked="true"]::after {
    transform: translateX(calc(var(--track-width) - var(--thumb) - 2 * var(--space-xxs) - 2px));
    background: var(--on-accent);
  }
</style>
