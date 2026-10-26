<!-- Capture's controls together, for Storybook: the toolbar, the readouts and the magnifier over a made-up
     frame (drawn with theme colours, so the story needs no picture file). -->
<script lang="ts">
  import Button from "../Button.svelte";
  import IconButton from "../IconButton.svelte";
  import Magnifier from "../Magnifier.svelte";
  import Readout from "../Readout.svelte";
  import Segmented from "../Segmented.svelte";
  import Toolbar from "../Toolbar.svelte";

  let kind = $state("image");
  let snapping = $state(true);
  let frame: HTMLCanvasElement | null = $state(null);
  let box = $state({ x: 1430, y: 1118, w: 420, h: 94 });

  const KINDS = [
    { value: "image", label: "Image" },
    { value: "region", label: "Region" },
    { value: "point", label: "Point" },
  ];

  function colour(name: string): string {
    return getComputedStyle(document.documentElement).getPropertyValue(name).trim();
  }

  $effect(() => {
    // a 64 x 64 corner of a "game": a panel edge and the top-left of a green button
    const canvas = document.createElement("canvas");
    canvas.width = 2000;
    canvas.height = 1400;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;
    ctx.fillStyle = colour("--bg");
    ctx.fillRect(0, 0, canvas.width, canvas.height);
    ctx.fillStyle = colour("--accent-2");
    ctx.fillRect(1380, 1080, 600, 6);
    ctx.fillStyle = colour("--ok");
    ctx.fillRect(1430, 1118, 420, 94);
    frame = canvas;
  });
</script>

<div class="stage">
  <div class="labels">
    <Readout kind="image" x={box.x} y={box.y} w={box.w} h={box.h} onchange={(value) => (box = { ...box, ...value })} />
    <Readout kind="region" x={344} y={243} w={1515} h={1082} />
    <Readout kind="point" x={1660} y={1165} />
  </div>
  {#if frame}
    <Magnifier {frame} x={1432} y={1120} shapes={[{ kind: "image", x: box.x, y: box.y, w: box.w, h: box.h }, { kind: "guide", x: 1430, y: 0 }]} />
  {/if}
  <Toolbar label="Capture tools" floating={false}>
    <b class="name">Bag.Equip</b>
    <Segmented items={KINDS} bind:value={kind} label="Kind" />
    <hr />
    <IconButton label="Snapping" icon="⌗" bind:pressed={snapping} />
    <IconButton label="Undo" icon="↶" action="edit.undo" />
    <IconButton label="Highlight" icon="◎" action="highlight.toggle" />
    <hr />
    <Button label="Save" variant="primary" action="capture.confirm" />
  </Toolbar>
</div>

<style>
  .stage {
    display: grid;
    gap: var(--space-xxl);
    justify-items: center;
  }
  .labels {
    display: flex;
    gap: var(--space-m);
  }
  .name {
    font: 600 var(--size-body) / 1 var(--font-strong);
    margin-right: var(--space-s);
    white-space: nowrap;
  }
</style>
