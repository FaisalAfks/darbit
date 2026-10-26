<!-- The zoomed pixels under the mouse, with the boxes, points and snap guides drawn on top (the old one hid a
     box that was under it), a pixel grid from 8x, the centre pixel outlined, and its colour and position.
     See docs/tasks/T09-capture-overlay.md step 6. -->
<script lang="ts">
  export interface Shape {
    kind: "image" | "region" | "point" | "guide";
    x: number;
    y: number;
    w?: number;
    h?: number;
  }

  const SIZE = 168; // px on screen
  const COLOURS: Record<Shape["kind"], string> = {
    image: "--kind-image",
    region: "--kind-region",
    point: "--kind-point",
    guide: "--accent",
  };

  let {
    frame,
    x,
    y,
    zoom = 8,
    shapes = [],
  }: { frame: CanvasImageSource | null; x: number; y: number; zoom?: number; shapes?: Shape[] } = $props();

  let canvas: HTMLCanvasElement | undefined = $state();
  let colour = $state("");

  function token(name: string): string {
    return getComputedStyle(document.documentElement).getPropertyValue(name).trim();
  }

  function hex(data: Uint8ClampedArray): string {
    let text = "";
    for (let i = 0; i < 3; i++) text += data[i].toString(16).padStart(2, "0");
    return text;
  }

  $effect(() => {
    if (!frame || !canvas) return;
    const ctx = canvas.getContext("2d", { willReadFrequently: true });
    if (!ctx) return;
    const span = SIZE / zoom; // screen pixels shown across
    const left = x - span / 2;
    const top = y - span / 2;
    ctx.imageSmoothingEnabled = false;
    ctx.clearRect(0, 0, SIZE, SIZE);
    ctx.drawImage(frame, left, top, span, span, 0, 0, SIZE, SIZE);
    colour = hex(ctx.getImageData(SIZE / 2, SIZE / 2, 1, 1).data);

    if (zoom >= 8) {
      ctx.strokeStyle = token("--line");
      ctx.lineWidth = 1;
      for (let i = 0; i <= span; i++) {
        const at = Math.round(i * zoom) + 0.5;
        ctx.beginPath();
        ctx.moveTo(at, 0);
        ctx.lineTo(at, SIZE);
        ctx.moveTo(0, at);
        ctx.lineTo(SIZE, at);
        ctx.stroke();
      }
    }

    for (const shape of shapes) {
      ctx.strokeStyle = token(COLOURS[shape.kind]);
      ctx.lineWidth = 2;
      const sx = (shape.x - left) * zoom;
      const sy = (shape.y - top) * zoom;
      ctx.beginPath();
      if (shape.kind === "point") {
        ctx.arc(sx, sy, 6, 0, Math.PI * 2);
      } else if (shape.kind === "guide") {
        ctx.moveTo(sx, 0);
        ctx.lineTo(sx, SIZE);
      } else {
        ctx.rect(sx, sy, (shape.w ?? 0) * zoom, (shape.h ?? 0) * zoom);
      }
      ctx.stroke();
    }

    ctx.strokeStyle = token("--text");
    ctx.lineWidth = 1;
    ctx.strokeRect(SIZE / 2 - zoom / 2 + 0.5, SIZE / 2 - zoom / 2 + 0.5, zoom - 1, zoom - 1);
  });
</script>

<figure class="mag appear" aria-label="Magnifier">
  <canvas bind:this={canvas} width={SIZE} height={SIZE}></canvas>
  <figcaption><span>{x}, {y}</span><span>{colour}</span></figcaption>
</figure>

<style>
  .mag {
    margin: 0;
    padding: 5px;
    border-radius: var(--radius-m);
    background: var(--glass-strong);
    border: 1px solid var(--line);
    box-shadow: var(--shadow);
    pointer-events: none;
  }
  canvas {
    display: block;
    border-radius: var(--radius-s);
    image-rendering: pixelated;
  }
  figcaption {
    display: flex;
    justify-content: space-between;
    gap: var(--space-2);
    padding: 3px 2px 0;
    font: var(--size-xs) / 1.4 var(--mono);
    color: var(--muted);
  }
</style>
