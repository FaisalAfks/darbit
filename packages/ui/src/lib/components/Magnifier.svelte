<!-- The zoomed pixels under the mouse, with the boxes, points and snap guides drawn on top
     (the old one hid a box that was under it). See docs/tasks/T09-capture-overlay.md step 6. -->
<script lang="ts">
  interface Shape { kind: "image" | "region" | "point" | "guide"; x: number; y: number; w?: number; h?: number }
  let { frame, x, y, zoom = 8, shapes = [] }:
    { frame: ImageBitmap | null; x: number; y: number; zoom?: number; shapes?: Shape[] } = $props();
  let canvas: HTMLCanvasElement | undefined = $state();
  const SIZE = 168;

  $effect(() => {
    if (!frame || !canvas) return;
    const ctx = canvas.getContext("2d")!;
    ctx.imageSmoothingEnabled = false;
    const span = SIZE / zoom;
    ctx.drawImage(frame, x - span / 2, y - span / 2, span, span, 0, 0, SIZE, SIZE);
    // TODO(T03): draw `shapes` in zoomed coordinates, outline the centre pixel, pixel grid at 8x and more
  });
</script>

<figure class="mag appear">
  <canvas bind:this={canvas} width={SIZE} height={SIZE}></canvas>
  <figcaption class="num">{x}, {y}</figcaption>
</figure>

<style>
  .mag {
    margin: 0; padding: 4px; border-radius: var(--radius-m); background: var(--glass-strong);
    border: 1px solid var(--line); box-shadow: var(--shadow); pointer-events: none;
  }
  canvas { display: block; border-radius: var(--radius-s); image-rendering: pixelated; }
  figcaption { text-align: center; font-size: var(--size-xs); color: var(--muted); padding-top: 2px; }
</style>
