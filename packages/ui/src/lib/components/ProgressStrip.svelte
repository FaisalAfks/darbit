<!-- A thin progress bar; what's left of a hidden card at the screen's edge. -->
<script lang="ts">
  let { done, total }: { done: number; total: number } = $props();
</script>

<div class="strip" role="progressbar" aria-valuenow={done} aria-valuemax={total}>
  <i style:transform="scaleX({total ? done / total : 0})"></i>
</div>

<style>
  .strip { height: 6px; border-radius: var(--radius-pill); background: var(--raised); overflow: hidden; }
  i {
    display: block; height: 100%; transform-origin: left;
    background: linear-gradient(90deg, var(--accent), var(--accent-2));
    transition: transform var(--move) var(--ease);
  }
</style>
