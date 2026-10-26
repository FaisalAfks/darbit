<!-- A thin progress bar; what's left of a hidden card at the screen's edge. -->
<script lang="ts">
  let { done, total }: { done: number; total: number } = $props();
</script>

<div class="strip" role="progressbar" aria-valuenow={done} aria-valuemax={total}>
  <i style:transform="scaleX({total ? done / total : 0})"></i>
</div>

<style>
  .strip { width: 100%; min-width: calc(5 * var(--space-xxxl)); height: var(--space-s-nudge); border-radius: var(--radius-pill); background: var(--raised); overflow: hidden; }
  i {
    display: block; height: 100%; transform-origin: left;
    background: linear-gradient(90deg, var(--accent), var(--accent-2));
    transition: transform var(--duration-normal) var(--curve-easy-ease);
  }
</style>
