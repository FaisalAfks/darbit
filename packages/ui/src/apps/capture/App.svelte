<!-- Capture, over the frozen game (decision 0013, round 7b): the shot dimmed outside the box, a box you can click,
     drag, resize, scale and nudge, a magnifier that follows the mouse, the guide card, and Test, which finds the
     boxed picture in its region and marks every match with its score. See docs/tasks/T09-capture-overlay.md. -->
<script lang="ts">
  import { frameImage, on, onFrame, request, type Frame } from "$lib/api";

  type Kind = "image" | "region" | "point";
  type Box = [number, number, number, number]; // x, y, w, h in pixels of the shot
  interface ItemInfo {
    name: string;
    kind: Kind;
    say: string;
    screen: string;
  }
  interface Hit {
    x: number;
    y: number;
    w: number;
    h: number;
    score: number;
  }

  const KINDS: Kind[] = ["image", "region", "point"];
  const MAG = 140; // px, the magnifier's size
  const ZOOM = 4;
  const CLICK = 4; // px of movement below which a press is a click
  const HANDLES = ["nw", "n", "ne", "w", "e", "sw", "s", "se"];

  let shot: ImageBitmap | null = $state(null);
  let shotW = $state(1);
  let shotH = $state(1);
  let viewW = $state(window.innerWidth);
  let viewH = $state(window.innerHeight);
  let canvas: HTMLCanvasElement | undefined = $state();
  let magCanvas: HTMLCanvasElement | undefined = $state();
  let items: ItemInfo[] = $state([]);
  let total = $state(0);
  let name = $state("");
  let kind: Kind = $state("image");
  let box: Box | null = $state(null);
  let region: Box | null = $state(null);
  let point: [number, number] | null = $state(null);
  let boxes: Box[] = []; // the candidates of the last click, smallest first
  let picked = 0;
  let lastClick: [number, number] | null = null;
  let undo: (Box | null)[] = [];
  let hits: Hit[] = $state([]);
  let testing = $state(false);
  let scanning = $state(false);
  let similarity = $state(0.85);
  let searched: Box | null = $state(null);
  let testMs = $state(0);
  let keysOpen = $state(false);
  let pinned = $state(false);
  let message = $state("");
  let mouse = { x: 0, y: 0 };
  let magQueued = false;
  let magStyle = $state("");
  let tagStyle = $state("");
  let colour = $state(""); // the pixel under the mouse, as hex
  let place = $state("");

  const scale = $derived(shotW / viewW); // shot pixels per screen pixel
  const current = $derived(items[0] ?? null);
  const guided = $derived(total > 0);
  const testable = $derived(kind === "image" && box !== null);

  function view(value: number): number {
    return value / scale;
  }

  function css(target: Box): string {
    return `left:${view(target[0])}px;top:${view(target[1])}px;width:${view(target[2])}px;height:${view(target[3])}px`;
  }

  /** The screen outside the box, as four plain panels: moving the box repaints only their edges. */
  function dimParts(target: Box): string[] {
    const left = view(target[0]);
    const top = view(target[1]);
    const right = view(target[0] + target[2]);
    const bottom = view(target[1] + target[3]);
    return [
      `left:0;top:0;right:0;height:${top}px`,
      `left:0;top:${bottom}px;right:0;bottom:0`,
      `left:0;top:${top}px;width:${left}px;height:${bottom - top}px`,
      `left:${right}px;top:${top}px;right:0;height:${bottom - top}px`,
    ];
  }

  async function loadFrame(): Promise<void> {
    const arrived = new Promise<Frame>((resolve) => {
      const stop = onFrame((frame) => {
        stop();
        resolve(frame);
      });
    });
    await request("capture.frame");
    const frame = await arrived;
    shot = await frameImage(frame);
    shotW = frame.header.w;
    shotH = frame.header.h;
    draw();
  }

  let pixels: CanvasRenderingContext2D | null = null; // a CPU copy of the shot, to read colours without a GPU stall

  function draw(): void {
    if (!canvas || !shot) return;
    canvas.width = shotW;
    canvas.height = shotH;
    canvas.getContext("2d")!.drawImage(shot, 0, 0);
    const copy = document.createElement("canvas");
    copy.width = shotW;
    copy.height = shotH;
    pixels = copy.getContext("2d", { willReadFrequently: true });
    pixels?.drawImage(shot, 0, 0);
  }

  let testName = $state(""); // opened from the Library to test this saved picture

  async function loadSession(): Promise<void> {
    const found = await request("capture.session");
    testName = found.test ?? "";
    items = found.items;
    if (!total) total = items.length;
    if (current) {
      name = current.name;
      kind = current.kind;
    }
  }

  function reset(): void {
    box = null;
    region = null;
    point = null;
    hits = [];
    testing = false;
    boxes = [];
    lastClick = null;
    undo = [];
  }

  async function begin(): Promise<void> {
    reset();
    await Promise.all([loadSession(), loadFrame()]);
    if (testName) {
      name = testName;
      await runTest();
    }
  }

  function setBox(next: Box | null): void {
    undo.push(box);
    if (undo.length > 50) undo.shift();
    box = next;
    hits = [];
    testing = false;
  }

  // ---- the magnifier: moved with transforms, at most once a frame
  function drawMag(): void {
    magQueued = false;
    if (!shot || !magCanvas) return;
    const sx = mouse.x * scale;
    const sy = mouse.y * scale;
    const context = magCanvas.getContext("2d")!;
    context.imageSmoothingEnabled = false;
    context.clearRect(0, 0, MAG, MAG);
    const span = MAG / ZOOM;
    context.drawImage(shot, sx - span / 2, sy - span / 2, span, span, 0, 0, MAG, MAG);
    const pixel = pixels ? pixels.getImageData(Math.round(sx), Math.round(sy), 1, 1).data : [0, 0, 0];
    colour = "#" + [pixel[0], pixel[1], pixel[2]].map((part) => part.toString(16).padStart(2, "0")).join("");
    place = `${Math.round(sx)}, ${Math.round(sy)}`;
    let left = mouse.x + 24;
    let top = mouse.y + 24;
    if (left + MAG > viewW - 8) left = mouse.x - MAG - 24;
    if (top + MAG + 26 > viewH - 8) top = mouse.y - MAG - 50;
    magStyle = `transform:translate(${left}px,${top}px)`;
    tagStyle = `transform:translate(${left}px,${top + MAG}px)`;
  }

  function follow(event: PointerEvent): void {
    if (pinned) return;
    mouse = { x: event.clientX, y: event.clientY };
    if (!magQueued) {
      magQueued = true;
      requestAnimationFrame(drawMag);
    }
  }

  // ---- clicking and dragging on the shot
  let press: { x: number; y: number; shift: boolean; ctrl: boolean } | null = $state(null);
  let drawing: Box | null = $state(null);

  function shotPoint(event: PointerEvent | MouseEvent): [number, number] {
    return [Math.round(event.clientX * scale), Math.round(event.clientY * scale)];
  }

  function stageDown(event: PointerEvent): void {
    if (event.button !== 0) return;
    press = { x: event.clientX, y: event.clientY, shift: event.shiftKey, ctrl: event.ctrlKey };
    (event.currentTarget as HTMLElement).setPointerCapture(event.pointerId);
  }

  function stageMove(event: PointerEvent): void {
    follow(event);
    if (!press) return;
    if (Math.abs(event.clientX - press.x) < CLICK && Math.abs(event.clientY - press.y) < CLICK) return;
    const x0 = Math.min(press.x, event.clientX) * scale;
    const y0 = Math.min(press.y, event.clientY) * scale;
    drawing = [Math.round(x0), Math.round(y0), Math.round(Math.abs(event.clientX - press.x) * scale), Math.round(Math.abs(event.clientY - press.y) * scale)];
  }

  async function stageUp(event: PointerEvent): Promise<void> {
    if (!press) return;
    const started = press;
    press = null;
    if (drawing) {
      if (started.shift && kind === "image") region = drawing;
      else setBox(drawing);
      drawing = null;
      return;
    }
    const [x, y] = shotPoint(event);
    if (started.ctrl || kind === "point") {
      point = [x, y];
      return;
    }
    await pickAt(x, y, 1);
  }

  async function pickAt(x: number, y: number, step: number): Promise<void> {
    const same = lastClick && Math.abs(lastClick[0] - x) < 3 && Math.abs(lastClick[1] - y) < 3;
    if (same && boxes.length) {
      picked = Math.max(0, Math.min(boxes.length - 1, picked + step));
      setBox(boxes[picked]);
      return;
    }
    lastClick = [x, y];
    const found = await request("capture.candidates", { x, y, kind }).catch((error: Error) => {
      message = error.message;
      return null;
    });
    if (!found) return;
    boxes = found.boxes;
    picked = found.start;
    setBox(boxes[picked]);
  }

  function stageMenu(event: MouseEvent): void {
    event.preventDefault();
    const [x, y] = shotPoint(event);
    pickAt(x, y, -1);
  }

  // ---- editing the selected box
  let drag: { handle: string; x: number; y: number; start: Box; point: [number, number] | null } | null = null;

  function boxDown(event: PointerEvent, handle: string): void {
    if (!box || event.button !== 0) return;
    event.stopPropagation();
    undo.push(box);
    drag = { handle, x: event.clientX, y: event.clientY, start: [...box] as Box, point: point ? [...point] : null };
    (event.currentTarget as HTMLElement).setPointerCapture(event.pointerId);
  }

  function boxMove(event: PointerEvent): void {
    follow(event);
    if (!drag || !box) return;
    const dx = (event.clientX - drag.x) * scale;
    const dy = (event.clientY - drag.y) * scale;
    const [x, y, w, h] = drag.start;
    const h0 = drag.handle;
    let next: Box = [x, y, w, h];
    if (h0 === "move") {
      next = [x + dx, y + dy, w, h];
      if (drag.point) point = [drag.point[0] + dx, drag.point[1] + dy];
    } else if (h0 === "point") {
      if (drag.point) point = [drag.point[0] + dx, drag.point[1] + dy];
      return;
    } else {
      if (h0.includes("w")) next = [x + dx, next[1], Math.max(2, w - dx), next[3]];
      if (h0.includes("e")) next = [next[0], next[1], Math.max(2, w + dx), next[3]];
      if (h0.includes("n")) next = [next[0], y + dy, next[2], Math.max(2, h - dy)];
      if (h0.includes("s")) next = [next[0], next[1], next[2], Math.max(2, h + dy)];
    }
    box = next.map(Math.round) as Box;
    hits = [];
  }

  function boxUp(): void {
    drag = null;
  }

  function boxWheel(event: WheelEvent): void {
    if (!box) return;
    event.preventDefault();
    const grow = event.deltaY < 0 ? 1.04 : 1 / 1.04;
    const [x, y, w, h] = box;
    const cx = x + w / 2;
    const cy = y + h / 2;
    setBox([Math.round(cx - (w * grow) / 2), Math.round(cy - (h * grow) / 2), Math.round(w * grow), Math.round(h * grow)]);
  }

  // ---- Test, Save, close
  async function runTest(): Promise<void> {
    if (!testName && (!testable || !box)) return;
    testing = true;
    scanning = false;
    hits = [];
    requestAnimationFrame(() => (scanning = true));
    const asked = testName && !box ? { name: testName, similarity } : { box, region, similarity };
    const result = await request("capture.test", asked).catch((error: Error) => {
      message = error.message;
      return null;
    });
    if (!result) return;
    searched = result.searched;
    testMs = result.ms;
    setTimeout(() => (hits = result.matches), 420);
  }

  async function save(): Promise<void> {
    if (!name.trim()) {
      message = "Give it a name first";
      return;
    }
    const center: [number, number] | null = box ? [box[0] + box[2] / 2, box[1] + box[3] / 2] : null;
    const payload = {
      name: name.trim(),
      kind,
      image: kind === "point" ? null : box,
      region: kind === "image" ? region : null,
      point: kind === "image" ? (point ?? center) : kind === "point" ? point : null,
    };
    const result = await request("capture.save", payload).catch((error: Error) => {
      message = error.message;
      return null;
    });
    if (!result) return;
    message = result.risky ? `Saved ${payload.name}, but something else looks alike` : `Saved ${payload.name}`;
    if (result.items.length) {
      items = result.items;
      name = items[0].name;
      kind = items[0].kind;
      reset();
      request("capture.next");
    } else {
      request("capture.close");
    }
  }

  function close(): void {
    if (testing) {
      if (testName) {
        request("capture.close");
        return;
      }
      testing = false;
      hits = [];
      return;
    }
    if (box) {
      reset();
      return;
    }
    request("capture.close");
  }

  function onkey(event: KeyboardEvent): void {
    if ((event.target as HTMLElement).tagName === "INPUT") {
      if (event.key === "Enter") save();
      if (event.key === "Escape") (event.target as HTMLElement).blur();
      return;
    }
    const arrows: Record<string, [number, number]> = { ArrowLeft: [-1, 0], ArrowRight: [1, 0], ArrowUp: [0, -1], ArrowDown: [0, 1] };
    if (arrows[event.key] && box) {
      event.preventDefault();
      const step = event.shiftKey ? 10 : 1;
      const [ax, ay] = arrows[event.key];
      const [x, y, w, h] = box;
      if (event.ctrlKey) setBox([x, y, Math.max(2, w + ax * step), Math.max(2, h + ay * step)]);
      else setBox([x + ax * step, y + ay * step, w, h]);
      return;
    }
    if (event.key === "?") keysOpen = true;
    else if (event.key === "Enter") save();
    else if (event.key === "Escape") close();
    else if (event.key === "Tab") {
      event.preventDefault();
      if (!guided) kind = KINDS[(KINDS.indexOf(kind) + 1) % KINDS.length];
    } else if (event.key.toLowerCase() === "t") runTest();
    else if (event.key === " ") request("capture.refreeze");
    else if (event.key.toLowerCase() === "z" && event.ctrlKey) {
      if (undo.length) box = undo.pop() ?? null;
    } else if (event.key.toLowerCase() === "z") pinned = !pinned;
    else if (event.key.toLowerCase() === "c" && box) point = [box[0] + box[2] / 2, box[1] + box[3] / 2];
  }

  function onkeyup(event: KeyboardEvent): void {
    if (event.key === "?") keysOpen = false;
  }

  $effect(() => {
    begin().catch((error: Error) => (message = error.message));
    const stopFrozen = on("capture.frozen", () => begin());
    function resized(): void {
      viewW = window.innerWidth;
      viewH = window.innerHeight;
    }
    window.addEventListener("resize", resized);
    return () => {
      stopFrozen();
      window.removeEventListener("resize", resized);
    };
  });

  $effect(() => {
    if (!message) return;
    const timer = setTimeout(() => (message = ""), 2600);
    return () => clearTimeout(timer);
  });
  function score(value: number | null | undefined): string {
    if (value === null || value === undefined) return "";
    if (value >= 0.995) return "1.00";
    return value.toFixed(2).slice(1); // .97
  }

</script>

<svelte:window onkeydown={onkey} {onkeyup} />

<div class="capture">
  <canvas class="shot" bind:this={canvas}></canvas>
  <div
    class="stage"
    role="presentation"
    onpointerdown={stageDown}
    onpointermove={stageMove}
    onpointerup={stageUp}
    oncontextmenu={stageMenu}
  ></div>
  {#if box}
    {@const dim = dimParts(box)}
    {#each dim as part, index (index)}<div class="dim" style={part}></div>{/each}
  {:else}
    <div class="dim" style="inset:0"></div>
  {/if}

  {#if region}
    <div class="region" style={css(region)}></div>
    <span class="readout reg" style="left:{view(region[0])}px;top:{view(region[1]) - 26}px">▭ search here · {region[2]} × {region[3]}</span>
  {/if}
  {#if drawing}<div class="drawing" class:reg={press?.shift} style={css(drawing)}></div>{/if}

  {#if box}
    <div
      class="sel"
      data-kind={kind}
      style={css(box)}
      role="presentation"
      onpointerdown={(event) => boxDown(event, "move")}
      onpointermove={boxMove}
      onpointerup={boxUp}
      onwheel={boxWheel}
    >
      {#each HANDLES as handle (handle)}
        <i class="handle {handle}" role="presentation" onpointerdown={(event) => boxDown(event, handle)}></i>
      {/each}
    </div>
    <span class="readout" style="left:{view(box[0])}px;top:{view(box[1] + box[3]) + 8}px">
      <b>{box[2]} × {box[3]}</b>
      {#if region}<em class:out={box[0] < region[0] || box[1] < region[1] || box[0] + box[2] > region[0] + region[2] || box[1] + box[3] > region[1] + region[3]}>inside ✓</em>{/if}
    </span>
  {/if}
  {#if point && kind !== "region"}
    <span
      class="point"
      style="left:{view(point[0])}px;top:{view(point[1])}px"
      role="presentation"
      onpointerdown={(event) => boxDown(event, "point")}
      onpointermove={boxMove}
      onpointerup={boxUp}
    ></span>
  {/if}

  {#if testing && searched}
    <div class="scan" class:go={scanning} style={css(searched)}></div>
  {/if}
  {#each hits as hit, index (index)}
    <div class="hit" class:out={hit.score < similarity} class:best={index === 0} style="{css([hit.x, hit.y, hit.w, hit.h])};animation-delay:{index * 90}ms">
      <b></b><b></b><b></b><b></b>
      <span class="fill"></span>
      <span class="score">{score(hit.score)}{#if index > 0 && hit.score < similarity}<small>look-alike</small>{/if}</span>
    </div>
  {/each}

  <div class="hint glass">hold <kbd>?</kbd> for keys</div>

  {#if guided && current}
    <div class="guide glass">
      <div class="title"><b>{current.screen || "Setup"}</b><small>{total - items.length + 1} / {total}</small></div>
      {#if current.say}<p>{current.say}</p>{/if}
      <p class="what"><span class="kind" data-kind={current.kind}>{current.kind}</span>{current.name}</p>
      <div class="dots">
        {#each Array(total) as _, index (index)}<i class:done={index < total - items.length} class:now={index === total - items.length}></i>{/each}
      </div>
    </div>
  {/if}

  {#if testing}
    <div class="result glass">
      {#if testName}<b class="testing-name">{testName}</b>{/if}
      <b>{hits.length} match{hits.length === 1 ? "" : "es"}</b>
      <span class="muted">{region ? "in its region" : "on the whole screen"} · {testMs} ms</span>
      <input type="range" min="0.5" max="1" step="0.01" bind:value={similarity} aria-label="Similarity" />
      <b>{score(similarity)}</b>
      <button class="icon" aria-label="Close the test" onclick={close}>✕</button>
    </div>
  {/if}

  <div class="toolbar glass">
    {#if guided}
      <span class="name">{name}{#if region}<small>▭ region</small>{/if}</span>
    {:else}
      <input class="name-input" bind:value={name} placeholder="Name, e.g. Lobby.Play" spellcheck="false" aria-label="Name" />
    {/if}
    <div class="kinds" role="radiogroup" aria-label="Kind">
      {#each KINDS as each (each)}
        <button role="radio" aria-checked={kind === each} data-kind={each} disabled={guided && kind !== each} onclick={() => (kind = each)}>
          {each === "image" ? "▣" : each === "region" ? "▭" : "✛"} {each}
        </button>
      {/each}
    </div>
    <span class="sep"></span>
    <button class="icon" class:on={pinned} aria-label="Pin the magnifier (Z)" title="Pin the magnifier (Z)" onclick={() => (pinned = !pinned)}>⌕</button>
    <button class="icon" aria-label="Undo (Ctrl+Z)" title="Undo (Ctrl+Z)" onclick={() => { if (undo.length) box = undo.pop() ?? null; }}>↶</button>
    <button class="icon" aria-label="Freeze again (Space)" title="Freeze again (Space)" onclick={() => request("capture.refreeze")}>⟳</button>
    <span class="sep"></span>
    <button class="test" class:ready={testable} disabled={!testable} onclick={runTest} title="Test (T)">◎ Test</button>
    <button class="save" onclick={save} title="Save (Enter)">Save</button>
    <button class="icon" aria-label="Close (Esc)" title="Close (Esc)" onclick={() => request("capture.close")}>✕</button>
  </div>

  <div class="keys glass" class:on={keysOpen}>
    <h6>Keys</h6>
    <span><kbd>click</kbd></span><span>box what's there (again: bigger, right-click: smaller)</span>
    <span><kbd>drag</kbd></span><span>draw a box; on the box: move it</span>
    <span><kbd>Shift</kbd>+<kbd>drag</kbd></span><span>where to search for the picture</span>
    <span><kbd>Ctrl</kbd>+<kbd>click</kbd></span><span>the click point (<kbd>C</kbd> centres it)</span>
    <span><kbd>wheel</kbd></span><span>grow or shrink the box</span>
    <span><kbd>←↑→↓</kbd></span><span>nudge 1 px (<kbd>Shift</kbd> 10), <kbd>Ctrl</kbd> resizes</span>
    <span><kbd>T</kbd> · <kbd>Enter</kbd> · <kbd>Esc</kbd></span><span>test · save · back</span>
    <span><kbd>Space</kbd> · <kbd>Z</kbd> · <kbd>Tab</kbd></span><span>freeze again · pin magnifier · kind</span>
  </div>

  {#if message}<div class="message glass">{message}</div>{/if}

  <canvas class="mag" width={MAG} height={MAG} bind:this={magCanvas} style={magStyle}></canvas>
  <div class="magtag" style={tagStyle}><i style:background={colour}></i>{place} · {colour}</div>
</div>

<style>
  :global(html),
  :global(body) {
    margin: 0;
    overflow: hidden;
    background: var(--bg);
  }
  .capture {
    position: fixed;
    inset: 0;
    cursor: crosshair;
    user-select: none;
    font-family: var(--font);
    color: var(--text);
  }
  .shot {
    position: absolute;
    inset: 0;
    width: 100%;
    height: 100%;
  }
  .stage {
    position: absolute;
    inset: 0;
  }
  .dim {
    position: absolute;
    background: var(--screen-dim);
    pointer-events: none;
  }
  .glass {
    background: var(--glass-strong);
    border: 1px solid var(--line);
    box-shadow: var(--shadow);
  }
  .region,
  .drawing {
    position: absolute;
    border: 2px dashed var(--kind-region);
    border-radius: var(--radius-m);
    pointer-events: none;
  }
  .drawing:not(.reg) {
    border: 2px solid var(--kind-image);
  }
  .sel {
    position: absolute;
    border: 2px solid var(--kind-image);
    border-radius: var(--radius-s);
    cursor: move;
    box-shadow: 0 0 0 1px color-mix(in oklab, var(--bg) 60%, transparent);
  }
  .sel[data-kind="region"] {
    border-color: var(--kind-region);
  }
  .handle {
    position: absolute;
    width: var(--space-m-nudge);
    height: var(--space-m-nudge);
    translate: -50% -50%;
    border-radius: var(--radius-s);
    background: var(--handle-fill);
    border: 1px solid var(--kind-image);
    transition: transform var(--duration-fast) var(--curve-easy-ease);
  }
  .handle:hover {
    transform: scale(1.35);
  }
  .nw { left: 0; top: 0; cursor: nwse-resize; }
  .n { left: 50%; top: 0; cursor: ns-resize; }
  .ne { left: 100%; top: 0; cursor: nesw-resize; }
  .w { left: 0; top: 50%; cursor: ew-resize; }
  .e { left: 100%; top: 50%; cursor: ew-resize; }
  .sw { left: 0; top: 100%; cursor: nesw-resize; }
  .s { left: 50%; top: 100%; cursor: ns-resize; }
  .se { left: 100%; top: 100%; cursor: nwse-resize; }
  .point {
    position: absolute;
    width: var(--space-l);
    height: var(--space-l);
    translate: -50% -50%;
    border: 2px solid var(--kind-point);
    border-radius: 50%;
    cursor: grab;
  }
  .readout {
    position: absolute;
    display: flex;
    gap: var(--space-xs);
    pointer-events: none;
    white-space: nowrap;
  }
  .readout b,
  .readout em,
  .readout.reg {
    padding: 0 var(--space-s);
    border-radius: var(--radius-s);
    font: 600 var(--size-caption) / var(--line-caption) var(--mono);
    font-style: normal;
  }
  .readout b {
    background: var(--kind-image);
    color: var(--on-accent);
  }
  .readout em {
    color: var(--ok);
    background: color-mix(in oklab, var(--ok) 18%, var(--bg));
  }
  .readout em.out {
    color: var(--danger);
  }
  .readout.reg {
    background: var(--kind-region);
    color: var(--on-accent);
  }
  .scan {
    position: absolute;
    overflow: hidden;
    border-radius: var(--radius-m);
    pointer-events: none;
  }
  .scan::before {
    content: "";
    position: absolute;
    top: 0;
    bottom: 0;
    left: 0;
    width: 30%;
    transform: translateX(-100%);
    background: linear-gradient(90deg, transparent, color-mix(in oklab, var(--accent) 25%, transparent), color-mix(in oklab, var(--accent) 50%, transparent));
    border-right: 2px solid var(--accent);
  }
  .scan.go::before {
    animation: sweep 420ms var(--curve-easy-ease) forwards;
  }
  @keyframes sweep {
    to {
      transform: translateX(340%);
    }
  }
  .hit {
    position: absolute;
    pointer-events: none;
    --c: var(--warn);
    animation: snap-in var(--duration-slow) var(--curve-decelerate) both;
  }
  .hit.best {
    --c: var(--ok);
  }
  .hit.out {
    opacity: 0.4;
    filter: grayscale(0.6);
  }
  .hit b {
    --bracket: 3px;
    position: absolute;
    width: var(--space-l);
    height: var(--space-l);
    border-color: var(--c);
    border-style: solid;
  }
  .hit b:nth-child(1) { left: calc(-1 * var(--space-xs)); top: calc(-1 * var(--space-xs)); border-width: var(--bracket) 0 0 var(--bracket); border-radius: var(--radius-s) 0 0 0; }
  .hit b:nth-child(2) { right: calc(-1 * var(--space-xs)); top: calc(-1 * var(--space-xs)); border-width: var(--bracket) var(--bracket) 0 0; border-radius: 0 var(--radius-s) 0 0; }
  .hit b:nth-child(3) { left: calc(-1 * var(--space-xs)); bottom: calc(-1 * var(--space-xs)); border-width: 0 0 var(--bracket) var(--bracket); border-radius: 0 0 0 var(--radius-s); }
  .hit b:nth-child(4) { right: calc(-1 * var(--space-xs)); bottom: calc(-1 * var(--space-xs)); border-width: 0 var(--bracket) var(--bracket) 0; border-radius: 0 0 var(--radius-s) 0; }
  .hit .fill {
    position: absolute;
    inset: 0;
    border-radius: var(--radius-s);
    background: color-mix(in oklab, var(--c) 16%, transparent);
    box-shadow: 0 0 var(--space-xl) color-mix(in oklab, var(--c) 55%, transparent);
    animation: breathe 1.6s ease-in-out infinite;
    will-change: opacity;
  }
  .hit .score {
    position: absolute;
    left: 50%;
    top: calc(-1 * var(--space-xxl));
    translate: -50% 0;
    padding: var(--space-xxs) var(--space-m);
    border-radius: var(--radius-pill);
    background: var(--c);
    color: var(--on-status);
    font: 800 var(--size-caption) / 1.2 var(--mono);
    white-space: nowrap;
  }
  .hit .score small {
    margin-left: var(--space-xs);
    font: 600 var(--size-caption) var(--font-strong);
  }
  @keyframes snap-in {
    from {
      opacity: 0;
      transform: scale(1.25);
    }
    to {
      opacity: 1;
      transform: none;
    }
  }
  @keyframes breathe {
    50% {
      opacity: 0.55;
    }
  }
  .hint {
    position: absolute;
    left: var(--space-l);
    top: var(--space-l);
    padding: var(--space-s) var(--space-m);
    border-radius: var(--radius-pill);
    color: var(--muted);
    font-size: var(--size-caption);
  }
  kbd {
    font: 600 var(--size-caption) / 1.4 var(--font-strong);
    padding: 0 var(--space-xs);
    border: 1px solid var(--line);
    border-bottom-width: 2px;
    border-radius: var(--radius-s);
    background: var(--raised);
    color: var(--text);
  }
  .guide {
    position: absolute;
    right: var(--space-l);
    top: var(--space-l);
    width: var(--width-sheet);
    display: grid;
    gap: var(--space-s);
    padding: var(--space-l);
    border-radius: var(--radius-xl);
    font-size: var(--size-body);
  }
  .guide .title {
    display: flex;
    justify-content: space-between;
    font-family: var(--font-strong);
  }
  .guide small {
    color: var(--muted);
    font-family: var(--mono);
  }
  .guide p {
    margin: 0;
  }
  .guide .what {
    display: flex;
    align-items: center;
    gap: var(--space-s);
    font: 700 var(--size-body) / 1.3 var(--mono);
  }
  .kind {
    padding: 0 var(--space-s);
    border-radius: var(--radius-pill);
    font: 700 var(--size-caption) / var(--line-caption) var(--font-strong);
    color: var(--kind-image);
    background: color-mix(in oklab, var(--kind-image) 16%, transparent);
  }
  .kind[data-kind="region"] {
    color: var(--kind-region);
    background: color-mix(in oklab, var(--kind-region) 16%, transparent);
  }
  .kind[data-kind="point"] {
    color: var(--kind-point);
    background: color-mix(in oklab, var(--kind-point) 16%, transparent);
  }
  .dots {
    display: flex;
    gap: var(--space-xxs);
  }
  .dots i {
    flex: 1;
    height: var(--space-xs);
    border-radius: var(--radius-pill);
    background: var(--raised-hover);
  }
  .dots i.done {
    background: var(--accent);
  }
  .dots i.now {
    background: var(--warn);
  }
  .result {
    position: absolute;
    left: 50%;
    top: var(--space-l);
    translate: -50% 0;
    display: flex;
    align-items: center;
    gap: var(--space-m);
    padding: var(--space-s) var(--space-s) var(--space-s) var(--space-l);
    border-radius: var(--radius-pill);
    font-size: var(--size-body);
    animation: drop var(--duration-normal) var(--curve-decelerate);
  }
  .testing-name {
    font-family: var(--mono);
    color: var(--kind-image);
  }
  .result input {
    width: calc(5 * var(--control-m));
    accent-color: var(--accent);
  }
  .muted {
    color: var(--muted);
  }
  .toolbar {
    position: absolute;
    left: 50%;
    bottom: var(--space-l);
    translate: -50% 0;
    display: flex;
    align-items: center;
    gap: var(--space-s);
    padding: var(--space-s);
    border-radius: var(--radius-pill);
    cursor: default;
    white-space: nowrap;
  }
  .name,
  .name-input {
    display: flex;
    align-items: center;
    gap: var(--space-s);
    height: var(--control-m);
    padding: 0 var(--space-m);
    border: 1px solid var(--line);
    border-radius: var(--radius-pill);
    background: color-mix(in oklab, var(--bg) 50%, transparent);
    color: var(--text);
    font: 700 var(--size-body) / 1 var(--mono);
  }
  .name small {
    color: var(--kind-region);
    font: 600 var(--size-caption) var(--font-strong);
  }
  .name-input {
    width: calc(7 * var(--control-m));
  }
  .name-input:focus {
    outline: none;
    border-color: var(--accent);
  }
  .kinds {
    display: flex;
    padding: var(--space-xxs);
    border-radius: var(--radius-pill);
    background: var(--raised);
  }
  .kinds button {
    height: calc(var(--control-m) - 2 * var(--space-xxs));
    padding: 0 var(--space-m);
    border: 0;
    border-radius: var(--radius-pill);
    background: none;
    color: var(--muted);
    font: 600 var(--size-caption) / 1 var(--font-strong);
    text-transform: capitalize;
    cursor: pointer;
  }
  .kinds button[aria-checked="true"] {
    background: var(--accent);
    color: var(--on-accent);
  }
  .kinds button[data-kind="region"][aria-checked="true"] {
    background: var(--kind-region);
  }
  .kinds button[data-kind="point"][aria-checked="true"] {
    background: var(--kind-point);
  }
  .kinds button:disabled {
    opacity: 0.35;
    cursor: default;
  }
  .sep {
    width: 1px;
    height: var(--space-xl);
    background: var(--line);
  }
  .icon {
    width: var(--control-m);
    height: var(--control-m);
    border: 0;
    border-radius: 50%;
    background: none;
    color: var(--muted);
    font-size: var(--size-body);
    cursor: pointer;
  }
  .icon:hover,
  .icon.on {
    background: var(--raised-hover);
    color: var(--text);
  }
  .test {
    position: relative;
    height: var(--control-m);
    padding: 0 var(--space-l);
    border: 1px solid color-mix(in oklab, var(--ok) 40%, transparent);
    border-radius: var(--radius-pill);
    background: color-mix(in oklab, var(--ok) 14%, transparent);
    color: var(--ok);
    font: 700 var(--size-body) / 1 var(--font-strong);
    cursor: pointer;
  }
  .test:disabled {
    opacity: 0.35;
    cursor: default;
  }
  .test.ready::before {
    content: "";
    position: absolute;
    inset: calc(-1 * var(--space-xs));
    border-radius: var(--radius-pill);
    border: 2px solid color-mix(in oklab, var(--ok) 55%, transparent);
    animation: ring 1.8s ease-out infinite;
  }
  @keyframes ring {
    from {
      opacity: 0.9;
      transform: scale(0.92);
    }
    to {
      opacity: 0;
      transform: scale(1.18);
    }
  }
  .save {
    height: var(--control-m);
    padding: 0 var(--space-xl);
    border: 0;
    border-radius: var(--radius-pill);
    background: var(--accent);
    color: var(--on-accent);
    font: 700 var(--size-body) / 1 var(--font-strong);
    cursor: pointer;
  }
  .keys {
    position: absolute;
    left: var(--space-l);
    bottom: calc(3 * var(--control-l));
    display: grid;
    grid-template-columns: auto 1fr;
    gap: var(--space-xs) var(--space-m);
    padding: var(--space-m) var(--space-l);
    border-radius: var(--radius-l);
    font-size: var(--size-caption);
    opacity: 0;
    translate: 0 var(--space-s);
    pointer-events: none;
    transition: opacity var(--duration-fast) var(--curve-easy-ease), translate var(--duration-fast) var(--curve-easy-ease);
  }
  .keys.on {
    opacity: 1;
    translate: 0 0;
  }
  .keys h6 {
    grid-column: 1 / -1;
    margin: 0;
    font: 700 var(--size-caption) / 1 var(--font-strong);
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: var(--muted);
  }
  .keys span:nth-child(odd) {
    color: var(--muted);
  }
  .message {
    position: absolute;
    left: 50%;
    bottom: calc(2 * var(--control-l));
    translate: -50% 0;
    padding: var(--space-s) var(--space-l);
    border-radius: var(--radius-pill);
    font-size: var(--size-body);
    animation: drop var(--duration-normal) var(--curve-decelerate);
  }
  .mag {
    --mag-size: 140px; /* MAG in the script */
    position: absolute;
    left: 0;
    top: 0;
    width: var(--mag-size);
    height: var(--mag-size);
    border-radius: var(--radius-l) var(--radius-l) 0 0;
    border: 1px solid var(--line);
    border-bottom: 0;
    box-shadow: var(--shadow);
    image-rendering: pixelated;
    pointer-events: none;
    will-change: transform;
    background: var(--bg);
  }
  .magtag {
    --mag-size: 140px;
    position: absolute;
    left: 0;
    top: 0;
    width: var(--mag-size);
    box-sizing: border-box;
    display: flex;
    justify-content: center;
    align-items: center;
    gap: var(--space-xs);
    padding: var(--space-xs) 0;
    border-radius: 0 0 var(--radius-l) var(--radius-l);
    border: 1px solid var(--line);
    border-top: 0;
    background: var(--glass-strong);
    font: 600 var(--size-caption) / 1 var(--mono);
    pointer-events: none;
    will-change: transform;
  }
  .magtag i {
    width: var(--space-m);
    height: var(--space-m);
    border-radius: var(--radius-s);
    border: 1px solid var(--text);
  }
  @keyframes drop {
    from {
      opacity: 0;
      transform: translateY(calc(-1 * var(--space-s)));
    }
  }
</style>
