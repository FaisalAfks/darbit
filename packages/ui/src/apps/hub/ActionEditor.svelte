<!-- The action editor (decision 0013, round 8d): one wide list built for long actions. Sticky, foldable sections;
     steps shown as keycaps, picture thumbnails and wait bars; a step's settings unfold under it; ＋ between rows;
     drag ⋮⋮ to reorder; Shift/Ctrl to pick many; calls to other actions with Peek and Open; Play with a playhead,
     breakpoints and stepping. Saving writes the action's Python (server/actions_api.py). -->
<script lang="ts">
  import { untrack } from "svelte";
  import { on, request } from "$lib/api";
  import { toast } from "$lib/toasts.svelte";

  interface StepData {
    id?: number;
    kind: string;
    args: Record<string, any>;
    note: string;
    line: number;
    source: string;
    children: StepData[];
  }
  interface SectionData {
    name: string;
    line: number;
    steps: StepData[];
  }
  interface ActionData {
    name: string;
    docstring: string;
    sections: SectionData[];
    calls: string[];
    used_by: string[];
    breakpoints: number[];
  }

  let { path, name, thumbnails, onback }: { path: string; name: string; thumbnails: Record<string, string>; onback: () => void } = $props();

  const KINDS: Record<string, { icon: string; tone: string }> = {
    key: { icon: "⌨", tone: "var(--accent-2)" },
    write: { icon: "✎", tone: "var(--accent-2)" },
    wait: { icon: "⏱", tone: "var(--muted)" },
    mouse: { icon: "🖱", tone: "var(--accent)" },
    check: { icon: "▣", tone: "var(--ok)" },
    if: { icon: "?", tone: "var(--ok)" },
    loop: { icon: "↻", tone: "var(--warn)" },
    call: { icon: "⤷", tone: "var(--slot-bot)" },
    code: { icon: "{ }", tone: "var(--faint)" },
    tape: { icon: "◉", tone: "var(--danger)" },
  };
  const SECTION_TONES = ["var(--accent)", "var(--accent-2)", "var(--ok)", "var(--warn)", "var(--danger)", "var(--slot-bot)", "var(--muted)"];
  const NEW_STEPS: { label: string; step: () => StepData }[] = [
    { label: "⌨ Press a key", step: () => blank("key", { verb: "press", keys: ["e"] }) },
    { label: "⏱ Wait", step: () => blank("wait", { seconds: 0.5 }) },
    { label: "🖱 Click a picture", step: () => blank("mouse", { verb: "click", target: "" }) },
    { label: "▣ Wait for a picture", step: () => blank("check", { verb: "wait for", target: "", timeout: 30 }) },
    { label: "? If a picture shows", step: () => blank("if", { verb: "if seen", target: "", timeout: 0.5 }) },
    { label: "↻ Repeat", step: () => blank("loop", { times: 3 }) },
    { label: "⤷ Run another action", step: () => blank("call", { name: "" }) },
  ];

  let stack: string[] = $state([untrack(() => name)]); // the editor is made again for another action
  let action = $state<ActionData | null>(null);
  let others: string[] = $state([]);
  let dirty = $state(false);
  let open: number | null = $state(null); // the step whose settings are unfolded
  let chosen = $state(new Set<number>());
  let lastChosen: number | null = null;
  let folded = $state(new Set<number>());
  let peeks: Record<number, StepData[]> = $state({});
  interface TapeSummary {
    seconds: number;
    moves: number;
    held: number;
    keys: number;
    clicks: number;
    scrolls: number;
    path: number[][];
    marks: { t: number; kind: string; text: string }[];
  }
  let tapes: Record<string, TapeSummary> = $state({}); // what each part of the tape holds, by "start-end"
  let splitAt = $state(0);
  let query = $state("");
  let jumpOpen = $state(false);
  let adding: number | null = $state(null); // insert after this step id (or -1-section for the top)
  let playing = $state(false);
  let pausedAt: number | null = $state(null);
  let lineNow: number | null = $state(null);
  let actionNow = $state("");
  let done = $state(new Set<number>());
  let dragging: number | null = $state(null);
  let overId: number | null = $state(null);
  let nextId = 1;
  let list: HTMLElement | undefined = $state();

  const current = $derived(stack[stack.length - 1]);
  const breakpoints = $derived(new Set(action?.breakpoints ?? []));
  const total = $derived(action ? action.sections.reduce((sum, section) => sum + count(section.steps), 0) : 0);

  function blank(kind: string, args: Record<string, any>): StepData {
    return { id: nextId++, kind, args, note: "", line: 0, source: "", children: [] };
  }

  function count(steps: StepData[]): number {
    let found = 0;
    for (const step of steps) found += 1 + count(step.children);
    return found;
  }

  function withIds(steps: StepData[]): StepData[] {
    for (const step of steps) {
      step.id = nextId++;
      withIds(step.children);
    }
    return steps;
  }

  async function load(): Promise<void> {
    const found = await request<ActionData>("actions.read", { path, name: current });
    for (const section of found.sections) withIds(section.steps);
    action = found;
    dirty = false;
    open = null;
    chosen = new Set();
    peeks = {};
    const listed = await request("actions.list", { path }).catch(() => []);
    others = listed.map((entry: { name: string }) => entry.name).filter((each: string) => each !== current);
    loadTapes();
  }

  // ---- the tape: recorded input played in parts
  function tapeKey(step: StepData): string {
    return `${step.args.start}-${step.args.end ?? ""}`;
  }

  function tapeSteps(steps: StepData[], found: StepData[]): StepData[] {
    for (const step of steps) {
      if (step.kind === "tape") found.push(step);
      tapeSteps(step.children, found);
    }
    return found;
  }

  function loadTapes(): void {
    if (!action) return;
    for (const section of action.sections) {
      for (const step of tapeSteps(section.steps, [])) loadTape(step);
    }
  }

  function loadTape(step: StepData): void {
    const key = tapeKey(step);
    if (tapes[key]) return;
    request<TapeSummary>("actions.tape", { path, name: current, start: step.args.start, end: step.args.end })
      .then((found) => (tapes[key] = found))
      .catch(() => {});
  }

  function tapeChanged(step: StepData): void {
    changed();
    loadTape(step);
  }

  function splitTape(step: StepData): void {
    const end = step.args.end ?? Infinity;
    if (!(splitAt > step.args.start && splitAt < end)) {
      toast(`Split between ${step.args.start} and ${step.args.end ?? "the end"} s`);
      return;
    }
    const found = locate(step.id!);
    if (!found) return;
    const second = blank("tape", { start: splitAt, end: step.args.end });
    step.args.end = splitAt;
    found.steps.splice(found.index + 1, 0, second);
    changed();
    loadTape(step);
    loadTape(second);
  }

  function pathPoints(summary: TapeSummary): string {
    return summary.path.map((point) => `${(point[0] * 100).toFixed(1)},${(point[1] * 60).toFixed(1)}`).join(" ");
  }

  async function save(): Promise<void> {
    if (!action) return;
    try {
      const saved = await request<ActionData>("actions.save", { path, name: current, sections: action.sections, docstring: action.docstring });
      for (const section of saved.sections) withIds(section.steps);
      action = saved;
      dirty = false;
      loadTapes();
      toast(`Saved ${current}`);
    } catch (error) {
      toast((error as Error).message);
    }
  }

  function changed(): void {
    dirty = true;
  }

  // ---- finding and moving steps
  function where(id: number, steps: StepData[]): { steps: StepData[]; index: number } | null {
    for (let index = 0; index < steps.length; index++) {
      if (steps[index].id === id) return { steps, index };
      const inner = where(id, steps[index].children);
      if (inner) return inner;
    }
    return null;
  }

  function locate(id: number): { steps: StepData[]; index: number } | null {
    if (!action) return null;
    for (const section of action.sections) {
      const found = where(id, section.steps);
      if (found) return found;
    }
    return null;
  }

  function insertAfter(id: number | null, sectionIndex: number, step: StepData): void {
    if (!action) return;
    if (id === null) action.sections[sectionIndex].steps.unshift(step);
    else {
      const found = locate(id);
      if (found) found.steps.splice(found.index + 1, 0, step);
    }
    adding = null;
    open = step.id ?? null;
    changed();
  }

  function remove(ids: number[]): void {
    for (const id of ids) {
      const found = locate(id);
      if (found) found.steps.splice(found.index, 1);
    }
    chosen = new Set();
    open = null;
    changed();
  }

  function duplicate(id: number): void {
    const found = locate(id);
    if (!found) return;
    const copy = withIds([JSON.parse(JSON.stringify(found.steps[found.index]))])[0];
    copy.line = 0;
    found.steps.splice(found.index + 1, 0, copy);
    changed();
  }

  function scaleWaits(factor: number): void {
    for (const id of chosen) {
      const found = locate(id);
      if (found && found.steps[found.index].kind === "wait") {
        const step = found.steps[found.index];
        step.args.seconds = Math.round(step.args.seconds * factor * 100) / 100;
      }
    }
    changed();
  }

  function drop(target: number): void {
    if (dragging === null || dragging === target) return;
    const from = locate(dragging);
    const to = locate(target);
    if (!from || !to) return;
    const [step] = from.steps.splice(from.index, 1);
    const again = locate(target);
    if (again) again.steps.splice(again.index, 0, step);
    dragging = null;
    overId = null;
    changed();
  }

  function pick(event: MouseEvent, step: StepData, flat: StepData[]): void {
    const id = step.id!;
    if (event.shiftKey && lastChosen !== null) {
      const a = flat.findIndex((each) => each.id === lastChosen);
      const b = flat.findIndex((each) => each.id === id);
      const next = new Set(chosen);
      for (let index = Math.min(a, b); index <= Math.max(a, b); index++) next.add(flat[index].id!);
      chosen = next;
    } else if (event.ctrlKey || event.metaKey) {
      const next = new Set(chosen);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      chosen = next;
    } else {
      chosen = new Set();
      open = open === id ? null : id;
    }
    lastChosen = id;
  }

  function flatten(steps: StepData[]): StepData[] {
    const found: StepData[] = [];
    for (const step of steps) {
      found.push(step);
      found.push(...flatten(step.children));
    }
    return found;
  }

  // ---- what a step shows
  function text(step: StepData): string {
    const args = step.args;
    if (step.kind === "key") return `${args.verb} ${(args.keys ?? []).join("+")}`;
    if (step.kind === "wait") return `wait ${args.seconds} s`;
    if (step.kind === "tape") return `replay ${args.start}–${args.end ?? "end"} s`;
    if (step.kind === "mouse" && (args.verb === "mouse_down" || args.verb === "mouse_up")) return `${args.button} button ${args.verb === "mouse_down" ? "down" : "up"}`;
    if (step.kind === "mouse" && args.verb === "move_by") return `move ${args.by[0]}, ${args.by[1]} in ${args.seconds} s`;
    if (step.kind === "mouse" && args.verb === "scroll") return `scroll ${args.notches > 0 ? "up" : "down"} ${Math.abs(args.notches)}`;
    if (step.kind === "mouse") return `${args.verb} ${Array.isArray(args.target) ? args.target.join(", ") : args.target}`;
    if (step.kind === "check" || step.kind === "if") return `${args.verb} ${args.target}`;
    if (step.kind === "loop") return "times" in args ? `repeat ${args.times}×` : `repeat until ${args.until} shows`;
    if (step.kind === "call") return String(args.name);
    if (step.kind === "write") return `write ${args.text}`;
    return step.source;
  }

  function matches(step: StepData): boolean {
    if (!query) return true;
    if (text(step).toLowerCase().includes(query.toLowerCase())) return true;
    return step.children.some(matches);
  }

  async function peek(step: StepData): Promise<void> {
    const id = step.id!;
    if (peeks[id]) {
      const next = { ...peeks };
      delete next[id];
      peeks = next;
      return;
    }
    const found = await request<ActionData>("actions.read", { path, name: step.args.name }).catch(() => null);
    if (!found) return;
    const steps: StepData[] = [];
    for (const section of found.sections) steps.push(...section.steps);
    peeks = { ...peeks, [id]: steps.slice(0, 6) };
  }

  async function openCall(target: string): Promise<void> {
    if (dirty) await save();
    stack = [...stack, target];
    await load();
    list?.scrollTo({ top: 0 });
  }

  async function back(to: number): Promise<void> {
    if (dirty) await save();
    stack = stack.slice(0, to + 1);
    await load();
  }

  // ---- breakpoints and play
  async function toggleBreak(step: StepData): Promise<void> {
    if (!action || !step.line) {
      toast("Save first: a new step has no line yet");
      return;
    }
    const next = new Set(breakpoints);
    if (next.has(step.line)) next.delete(step.line);
    else next.add(step.line);
    const saved = await request("actions.breakpoints", { path, name: current, lines: [...next] });
    action.breakpoints = saved.breakpoints;
  }

  async function play(stepping = false): Promise<void> {
    if (dirty) await save();
    done = new Set();
    pausedAt = null;
    try {
      await request("actions.play", { path, name: current, stepping });
      playing = true;
    } catch (error) {
      toast((error as Error).message);
    }
  }

  function control(what: string): void {
    request("actions.control", { what });
    if (what !== "stop") pausedAt = null;
  }

  function follow(line: number): void {
    const row = list?.querySelector(`[data-line="${line}"]`) as HTMLElement | null;
    if (row && list) list.scrollTo({ top: row.offsetTop - list.clientHeight / 2, behavior: "smooth" });
  }

  function sectionDone(section: SectionData): number {
    const steps = flatten(section.steps);
    if (!steps.length) return 0;
    return steps.filter((step) => done.has(step.line)).length / steps.length;
  }

  $effect(() => {
    current;
    load().catch((error: Error) => toast(error.message));
  });

  $effect(() => {
    const stops = [
      on("action.line", (data) => {
        actionNow = data.action;
        if (data.action === current && lineNow !== null) done = new Set([...done, lineNow]);
        lineNow = data.line;
        if (data.action === current) follow(data.line);
      }),
      on("action.paused", (data) => {
        pausedAt = data.line;
        lineNow = data.line;
      }),
      on("action.ended", (data) => {
        playing = false;
        pausedAt = null;
        lineNow = null;
        toast(data.status === "done" ? `${data.action} finished` : data.status === "stopped" ? `${data.action} stopped` : `${data.action} failed: ${data.reason}`);
      }),
    ];
    return () => stops.forEach((stop) => stop());
  });
</script>

{#snippet what(step: StepData)}
  {@const args = step.args}
  {#if step.kind === "key"}
    <span class="verb">{args.verb}</span><span class="keycaps">{#each (args.keys ?? []).join("+").split("+") as key, index (index)}<kbd>{key}</kbd>{/each}</span>
  {:else if step.kind === "wait"}
    <span class="verb">wait</span><span class="dur"><i style:width="{Math.min(12, args.seconds) * 4}%"></i>{args.seconds} s</span>
  {:else if step.kind === "tape"}
    {@const summary = tapes[tapeKey(step)]}
    <span class="verb">replay</span><span class="tgt">{args.start} – {args.end ?? "end"} s</span>
    {#if summary}
      <small>{summary.moves} mouse moves{summary.held ? ` (${summary.held} turning the camera)` : ""} · {summary.keys} keys · {summary.clicks} clicks{summary.scrolls ? ` · ${summary.scrolls} scrolls` : ""}</small>
      <span class="tape">
        <svg viewBox="0 0 100 60" preserveAspectRatio="none" aria-hidden="true"><polyline points={pathPoints(summary)} /></svg>
        <span class="marks">{#each summary.marks as mark, index (index)}<i data-kind={mark.kind} style:left="{summary.seconds ? (mark.t / summary.seconds) * 100 : 0}%" title="{mark.text} at {mark.t} s"></i>{/each}</span>
      </span>
    {/if}
  {:else if step.kind === "mouse" && (args.verb === "mouse_down" || args.verb === "mouse_up")}
    <span class="verb">{args.button} button {args.verb === "mouse_down" ? "down" : "up"}</span><span class="tgt">{Array.isArray(args.target) ? `${args.target[0]}, ${args.target[1]}` : "where it is"}</span>
  {:else if step.kind === "mouse" && args.verb === "scroll"}
    <span class="verb">scroll {args.notches > 0 ? "up" : "down"}</span><span class="tgt">{Math.abs(args.notches)}</span>
  {:else if step.kind === "mouse" && args.verb === "move_by"}
    <span class="verb">move</span><span class="tgt">{args.by[0]}, {args.by[1]}</span><small>in {args.seconds} s</small>
  {:else if step.kind === "mouse" || step.kind === "check" || step.kind === "if"}
    <span class="verb">{step.kind === "mouse" ? args.verb.replace("_", " ") : args.verb}</span>
    {#if typeof args.target === "string" && thumbnails[args.target]}<img class="thumb" src={thumbnails[args.target]} alt="" />{/if}
    <span class="tgt">{Array.isArray(args.target) ? `${args.target[0]}, ${args.target[1]}` : args.target || "pick a picture"}</span>
    {#if args.timeout}<small>up to {args.timeout} s</small>{/if}
  {:else if step.kind === "loop"}
    <span class="verb">{"times" in args ? `repeat ${args.times}×` : "repeat until"}</span>{#if !("times" in args)}<span class="tgt">{args.until} shows</span>{/if}
  {:else if step.kind === "call"}
    <span class="callchip">⤷ {args.name || "pick an action"}
      {#if args.name}<button class="mini" onclick={(event) => { event.stopPropagation(); peek(step); }}>{peeks[step.id!] ? "Hide" : "Peek"}</button><button class="mini" onclick={(event) => { event.stopPropagation(); openCall(args.name); }}>Open ›</button>{/if}
    </span>
  {:else if step.kind === "write"}
    <span class="verb">write</span><span class="tgt">“{args.text}”</span>
  {:else}
    <code>{step.source}</code>
  {/if}
{/snippet}

{#snippet settings(step: StepData)}
  {@const args = step.args}
  <div class="settings">
    {#if step.kind === "key"}
      <label>Do <select bind:value={args.verb} onchange={changed}><option>press</option><option>hold</option><option>release</option></select></label>
      <label>Keys <input value={(args.keys ?? []).join("+")} oninput={(event) => { const keys = event.currentTarget.value.split("+").map((key) => key.trim()).filter(Boolean); args.keys = args.verb === "press" ? [keys.join("+")] : keys; changed(); }} /></label>
    {:else if step.kind === "wait"}
      <label>Seconds <input type="number" min="0" step="0.01" bind:value={args.seconds} oninput={changed} /></label>
    {:else if step.kind === "tape"}
      <label>From <input type="number" min="0" step="0.01" bind:value={args.start} oninput={() => tapeChanged(step)} /> s</label>
      <label>To <input type="number" min="0" step="0.01" bind:value={args.end} oninput={() => tapeChanged(step)} /> s</label>
      <label>Split at <input type="number" min="0" step="0.01" bind:value={splitAt} /> s</label>
      <button class="mini" onclick={() => splitTape(step)}>Split</button>
    {:else if step.kind === "mouse" && args.verb === "scroll"}
      <label>Notches <input type="number" step="1" bind:value={args.notches} oninput={changed} /> (up is positive)</label>
    {:else if step.kind === "mouse" && args.verb === "move_by"}
      <label>Right <input type="number" step="1" bind:value={args.by[0]} oninput={changed} /></label>
      <label>Down <input type="number" step="1" bind:value={args.by[1]} oninput={changed} /></label>
      <label>Over <input type="number" min="0" step="0.01" bind:value={args.seconds} oninput={changed} /> s</label>
    {:else if step.kind === "mouse"}
      <label>Do <select bind:value={args.verb} onchange={changed}><option>click</option><option>double_click</option><option>right_click</option><option>hover</option></select></label>
      <label>On <input list="pictures" value={Array.isArray(args.target) ? args.target.join(", ") : args.target} oninput={(event) => { const value = event.currentTarget.value; const parts = value.split(","); args.target = parts.length === 2 && parts.every((part) => part.trim() !== "" && !isNaN(Number(part))) ? parts.map((part) => Number(part)) : value; changed(); }} placeholder="a picture's name, or x, y" /></label>
    {:else if step.kind === "check" || step.kind === "if"}
      {#if step.kind === "check"}<label>Do <select bind:value={args.verb} onchange={changed}><option>wait for</option><option>until gone</option></select></label>{/if}
      <label>Picture <input list="pictures" bind:value={args.target} oninput={changed} /></label>
      <label>Up to <input type="number" min="0" step="0.5" bind:value={args.timeout} oninput={changed} /> s</label>
    {:else if step.kind === "loop"}
      {#if "times" in args}<label>Times <input type="number" min="1" bind:value={args.times} oninput={changed} /></label>{:else}<label>Until <input list="pictures" bind:value={args.until} oninput={changed} /> shows</label>{/if}
    {:else if step.kind === "call"}
      <label>Action <select bind:value={args.name} onchange={changed}>{#each others as other (other)}<option>{other}</option>{/each}</select></label>
    {:else if step.kind === "write"}
      <label>Text <input bind:value={args.text} oninput={changed} /></label>
    {:else}
      <label class="wide">Python <textarea bind:value={step.source} oninput={changed} rows="3"></textarea></label>
    {/if}
    <label class="wide">Note <input bind:value={step.note} oninput={changed} placeholder="shown in the run panel; saved as the comment on its line" /></label>
    <span class="grow"></span>
    <button class="tool" onclick={() => duplicate(step.id!)}>⧉ Duplicate</button>
    <button class="tool bad" onclick={() => remove([step.id!])}>⌫ Delete</button>
  </div>
{/snippet}

{#snippet rows(steps: StepData[], sectionIndex: number, flat: StepData[], depth: number)}
  {#each steps.filter(matches) as step (step.id)}
    {@const kind = KINDS[step.kind] ?? KINDS.code}
    <div
      class="row"
      class:on={open === step.id || chosen.has(step.id!)}
      class:now={lineNow !== null && actionNow === current && step.line === lineNow}
      class:held={pausedAt !== null && step.line === pausedAt && actionNow === current}
      class:done={done.has(step.line) && actionNow === current}
      class:over={overId === step.id}
      class:lifted={dragging === step.id}
      data-line={step.line}
      style:--tone={kind.tone}
      style:--depth={depth}
      role="presentation"
      draggable="true"
      ondragstart={() => (dragging = step.id!)}
      ondragover={(event) => { event.preventDefault(); overId = step.id!; }}
      ondragleave={() => (overId = null)}
      ondrop={() => drop(step.id!)}
      ondragend={() => { dragging = null; overId = null; }}
      onclick={(event) => pick(event, step, flat)}
    >
      <span class="grip" aria-hidden="true">⋮⋮</span>
      <span class="n">{step.line || "new"}</span>
      <span class="ic">{kind.icon}</span>
      <span class="what">{@render what(step)}</span>
      {#if step.note}<small class="note">{step.note}</small>{:else}<span></span>{/if}
      <button class="bp" class:set={breakpoints.has(step.line)} aria-label="Breakpoint" title="Breakpoint" onclick={(event) => { event.stopPropagation(); toggleBreak(step); }}></button>
      <button class="between" aria-label="Add a step after this" title="Add a step after this" onclick={(event) => { event.stopPropagation(); adding = adding === step.id ? null : step.id!; }}>＋</button>
    </div>
    {#if adding === step.id}
      <div class="adder" style:--depth={depth}>{#each NEW_STEPS as option (option.label)}<button class="tool" onclick={() => insertAfter(step.id!, sectionIndex, option.step())}>{option.label}</button>{/each}</div>
    {/if}
    {#if open === step.id}{@render settings(step)}{/if}
    {#if peeks[step.id!]}
      <div class="peek" style:--depth={depth}>
        <div class="peekhead"><span>Inside <b>{step.args.name}</b> · read-only</span><button class="tool" onclick={() => openCall(step.args.name)}>Open to edit ›</button></div>
        {#each peeks[step.id!] as inner, index (index)}<div class="row ghost" style:--tone={(KINDS[inner.kind] ?? KINDS.code).tone}><span></span><span class="n">{inner.line}</span><span class="ic">{(KINDS[inner.kind] ?? KINDS.code).icon}</span><span class="what">{@render what(inner)}</span></div>{/each}
      </div>
    {/if}
    {#if step.kind === "if" || step.kind === "loop"}
      <div class="block" class:loop={step.kind === "loop"} style:--depth={depth}>
        {@render rows(step.children, sectionIndex, flat, depth + 1)}
        {#if !step.children.length}<button class="tool empty-add" onclick={() => { step.children.push(blank("wait", { seconds: 0.5 })); changed(); }}>＋ a step inside</button>{/if}
      </div>
    {/if}
  {/each}
{/snippet}

<datalist id="pictures">{#each Object.keys(thumbnails) as picture (picture)}<option value={picture}></option>{/each}</datalist>

{#if action}
  {@const flat = action.sections.flatMap((section) => flatten(section.steps))}
  <div class="editor">
    <div class="crumbs">
      <button class="back" aria-label="Back" onclick={() => (stack.length > 1 ? back(stack.length - 2) : onback())}>←</button>
      <button class="link" onclick={onback}>Library › Actions</button>
      {#each stack as each, index (index)}
        › {#if index === stack.length - 1}<b>{each}</b>{:else}<button class="link" onclick={() => back(index)}>{each}</button>{/if}
      {/each}
    </div>
    <div class="head">
      <span class="pill">{total} steps</span>
      <span class="pill">{action.sections.length} section{action.sections.length === 1 ? "" : "s"}</span>
      {#if action.used_by.length}<span class="muted">used by {action.used_by.join(", ")}</span>{/if}
      <span class="grow"></span>
      {#if playing}
        {#if pausedAt !== null}
          <button class="tool" onclick={() => control("step")}>⤼ Step</button>
          <button class="tool" onclick={() => control("resume")}>▶ Go on</button>
        {/if}
        <button class="tool bad" onclick={() => control("stop")}>■ Stop</button>
      {:else}
        <button class="tool" onclick={() => play(true)} title="Run one line at a time">⤼ Step through</button>
        <button class="play" onclick={() => play(false)}>▶ Play</button>
      {/if}
    </div>

    {#if chosen.size > 1}
      <div class="bulk">
        <b>{chosen.size} picked</b>
        <button class="tool" onclick={() => scaleWaits(0.8)}>⏱ Waits × 0.8</button>
        <button class="tool" onclick={() => scaleWaits(1.25)}>⏱ Waits × 1.25</button>
        <button class="tool bad" onclick={() => remove([...chosen])}>⌫ Delete</button>
        <button class="tool" onclick={() => (chosen = new Set())}>Done</button>
      </div>
    {/if}

    <div class="box">
      <div class="bar">
        <input class="search" bind:value={query} placeholder="⌕ Search steps" aria-label="Search steps" />
        <span class="legend">
          {#each ["key", "mouse", "check", "wait", "call"] as kind (kind)}<span style:--tone={KINDS[kind].tone}><i></i>{kind === "key" ? "keys" : kind === "mouse" ? "clicks" : kind === "check" ? "checks" : kind === "wait" ? "waits" : "actions"}</span>{/each}
        </span>
        <span class="grow"></span>
        <div class="jump">
          <button class="tool" onclick={() => (jumpOpen = !jumpOpen)}>Jump to ▾</button>
          {#if jumpOpen}
            <div class="jumpmenu">
              {#each action.sections as section, index (index)}
                <button onclick={() => { jumpOpen = false; list?.querySelector(`#section-${index}`)?.scrollIntoView({ behavior: "smooth" }); }} style:--tone={SECTION_TONES[index % SECTION_TONES.length]}><i></i>{section.name || "Start"}<small>{count(section.steps)}</small></button>
              {/each}
            </div>
          {/if}
        </div>
      </div>
      <div class="list" bind:this={list}>
        {#each action.sections as section, sectionIndex (sectionIndex)}
          <button class="section" class:closed={folded.has(sectionIndex)} id="section-{sectionIndex}" style:--tone={SECTION_TONES[sectionIndex % SECTION_TONES.length]} onclick={() => { const next = new Set(folded); if (next.has(sectionIndex)) next.delete(sectionIndex); else next.add(sectionIndex); folded = next; }}>
            <span class="fold">▾</span><span class="dot"></span>{section.name || "Start"}
            {#if section.name}<code>with d.step("{section.name}")</code>{/if}
            <span class="grow"></span>
            {#if playing}<span class="progress"><i style:width="{sectionDone(section) * 100}%"></i></span>{/if}
            <small>{count(section.steps)} steps</small>
          </button>
          {#if !folded.has(sectionIndex)}
            <div class="sectionbody">
              {@render rows(section.steps, sectionIndex, flat, 0)}
              {#if !section.steps.length}<button class="tool empty-add" onclick={() => insertAfter(null, sectionIndex, blank("wait", { seconds: 0.5 }))}>＋ First step</button>{/if}
            </div>
          {/if}
        {/each}
      </div>
    </div>
  </div>

  {#if dirty}
    <div class="savebar" role="status">
      <span>Unsaved changes</span>
      <button class="tool" onclick={load}>Undo all</button>
      <button class="play" onclick={save}>Save</button>
    </div>
  {/if}
{/if}

<style>
  .editor {
    display: grid;
    gap: var(--space-m);
    max-width: calc(4 * var(--width-sheet));
    margin: 0 auto;
    width: 100%;
    padding-bottom: calc(2 * var(--control-l));
  }
  .crumbs {
    display: flex;
    align-items: center;
    gap: var(--space-s);
    color: var(--muted);
    flex-wrap: wrap;
  }
  .crumbs b {
    color: var(--text);
    font: 700 var(--size-title3) / var(--line-title3) var(--font-strong);
    animation: slide var(--duration-normal) var(--curve-decelerate);
  }
  .back {
    width: var(--control-m);
    height: var(--control-m);
    border: 0;
    border-radius: 50%;
    background: var(--raised);
    color: var(--text);
    cursor: pointer;
  }
  .link {
    border: 0;
    background: none;
    color: var(--muted);
    font: inherit;
    cursor: pointer;
    padding: var(--space-xxs) var(--space-s);
    border-radius: var(--radius-pill);
  }
  .link:hover {
    background: var(--raised);
    color: var(--text);
  }
  .head,
  .bulk {
    display: flex;
    align-items: center;
    gap: var(--space-s);
    flex-wrap: wrap;
  }
  .bulk {
    padding: var(--space-s) var(--space-m);
    border-radius: var(--radius-l);
    background: color-mix(in oklab, var(--accent) 12%, transparent);
    border: 1px solid color-mix(in oklab, var(--accent) 35%, transparent);
    animation: slide var(--duration-normal) var(--curve-decelerate);
  }
  .pill {
    padding: var(--space-xxs) var(--space-m);
    border-radius: var(--radius-pill);
    background: var(--raised);
    font: 600 var(--size-caption) / 1.4 var(--font-strong);
  }
  .muted {
    color: var(--muted);
    font-size: var(--size-caption);
  }
  .grow {
    flex: 1;
  }
  .tool {
    height: var(--control-m);
    padding: 0 var(--space-m);
    border: 0;
    border-radius: var(--radius-pill);
    background: var(--raised);
    color: var(--text);
    font: 600 var(--size-caption) / 1 var(--font-strong);
    cursor: pointer;
    white-space: nowrap;
  }
  .tool:hover {
    background: var(--raised-hover);
  }
  .tool.bad {
    color: var(--danger);
  }
  .play {
    height: var(--control-m);
    padding: 0 var(--space-l);
    border: 0;
    border-radius: var(--radius-pill);
    background: linear-gradient(135deg, var(--accent), var(--accent-2));
    color: var(--on-accent);
    font: 700 var(--size-caption) / 1 var(--font-strong);
    cursor: pointer;
    box-shadow: 0 var(--space-xs) var(--space-l) color-mix(in oklab, var(--accent) 30%, transparent);
  }
  .box {
    display: grid;
    padding: var(--space-s);
    border-radius: var(--radius-xl);
    background: var(--glass);
    border: 1px solid var(--line);
  }
  .bar {
    display: flex;
    align-items: center;
    gap: var(--space-m);
    padding: var(--space-xs) var(--space-s) var(--space-s);
  }
  .search {
    width: calc(7 * var(--control-m));
    padding: var(--space-s) var(--space-m);
    border: 1px solid var(--line);
    border-radius: var(--radius-pill);
    background: var(--raised);
    color: var(--text);
    font: inherit;
    font-size: var(--size-caption);
  }
  .legend {
    display: flex;
    gap: var(--space-m);
    color: var(--muted);
    font-size: var(--size-caption);
  }
  .legend i {
    display: inline-block;
    width: var(--space-s);
    height: var(--space-s);
    margin-right: var(--space-xs);
    border-radius: var(--radius-s);
    background: var(--tone);
  }
  .jump {
    position: relative;
  }
  .jumpmenu {
    position: absolute;
    right: 0;
    top: calc(100% + var(--space-xs));
    z-index: 6;
    display: grid;
    min-width: calc(6 * var(--control-l));
    padding: var(--space-xs);
    border-radius: var(--radius-l);
    background: var(--glass-strong);
    border: 1px solid var(--line);
    box-shadow: var(--shadow);
  }
  .jumpmenu button {
    display: grid;
    grid-template-columns: var(--space-s) 1fr auto;
    gap: var(--space-s);
    align-items: center;
    padding: var(--space-s) var(--space-m);
    border: 0;
    border-radius: var(--radius-m);
    background: none;
    color: var(--text);
    font: inherit;
    font-size: var(--size-caption);
    text-align: left;
    cursor: pointer;
  }
  .jumpmenu button:hover {
    background: var(--raised);
  }
  .jumpmenu i {
    width: var(--space-s);
    height: var(--space-s);
    border-radius: 50%;
    background: var(--tone);
  }
  .list {
    max-height: calc(100vh - 14 * var(--space-xl));
    min-height: calc(6 * var(--control-l));
    overflow: auto;
    padding: 0 var(--space-xs) var(--space-xl);
  }
  .section {
    position: sticky;
    top: 0;
    z-index: 3;
    display: flex;
    align-items: center;
    gap: var(--space-m);
    width: 100%;
    margin-top: var(--space-s);
    padding: var(--space-s) var(--space-m);
    border: 1px solid color-mix(in oklab, var(--tone) 35%, transparent);
    border-radius: var(--radius-l);
    background: linear-gradient(90deg, color-mix(in oklab, var(--tone) 20%, var(--glass-strong)), var(--glass-strong) 60%);
    color: var(--text);
    font: 700 var(--size-body) / 1.3 var(--font-strong);
    cursor: pointer;
    text-align: left;
  }
  .section .fold {
    color: var(--muted);
    transition: rotate var(--duration-fast) var(--curve-easy-ease);
  }
  .section.closed .fold {
    rotate: -90deg;
  }
  .section .dot {
    width: var(--space-s);
    height: var(--space-s);
    border-radius: 50%;
    background: var(--tone);
    box-shadow: 0 0 var(--space-s) var(--tone);
  }
  .section code {
    color: var(--muted);
    font: 500 var(--size-caption) / 1 var(--mono);
    background: none;
  }
  .section small {
    color: var(--muted);
    font: 600 var(--size-caption) var(--font-strong);
  }
  .progress {
    width: calc(3 * var(--control-m));
    height: var(--space-xs);
    border-radius: var(--radius-pill);
    background: var(--raised);
    overflow: hidden;
  }
  .progress i {
    display: block;
    height: 100%;
    background: var(--tone);
    transition: width var(--duration-normal) var(--curve-decelerate);
  }
  .sectionbody {
    animation: slide var(--duration-normal) var(--curve-decelerate);
  }
  .row {
    position: relative;
    display: grid;
    grid-template-columns: var(--space-l) calc(1.5 * var(--control-m)) var(--control-s) 1fr auto var(--space-l);
    gap: var(--space-m);
    align-items: center;
    min-height: var(--control-l);
    margin-left: calc(var(--depth, 0) * var(--space-xl));
    padding: 0 var(--space-m);
    border-radius: var(--radius-m);
    cursor: pointer;
    transition: background var(--duration-fast) var(--curve-easy-ease);
  }
  .row::before {
    content: "";
    position: absolute;
    left: 0;
    top: var(--space-s);
    bottom: var(--space-s);
    width: var(--space-xxs);
    border-radius: var(--radius-s);
    background: var(--tone);
    opacity: 0;
    transition: opacity var(--duration-fast) var(--curve-easy-ease);
  }
  .row:hover {
    background: var(--raised);
  }
  .row:hover::before {
    opacity: 0.8;
  }
  .row.on {
    background: color-mix(in oklab, var(--accent) 14%, transparent);
  }
  .row.on::before {
    opacity: 1;
    background: var(--accent);
  }
  .row.now {
    background: linear-gradient(90deg, color-mix(in oklab, var(--ok) 24%, transparent), color-mix(in oklab, var(--ok) 4%, transparent));
  }
  .row.now::before {
    opacity: 1;
    background: var(--ok);
    box-shadow: 0 0 var(--space-m) var(--ok);
  }
  .row.held {
    animation: flash 0.6s ease-in-out 3;
  }
  .row.done {
    opacity: 0.55;
  }
  .row.over {
    box-shadow: inset 0 2px 0 var(--accent);
  }
  .row.lifted {
    opacity: 0.35;
  }
  .row.ghost {
    cursor: default;
    min-height: var(--control-m);
  }
  .grip {
    color: var(--faint);
    opacity: 0;
    cursor: grab;
    font-size: var(--size-caption);
  }
  .row:hover .grip {
    opacity: 0.8;
  }
  .n {
    color: var(--faint);
    font: 600 var(--size-caption) / 1 var(--mono);
    text-align: right;
  }
  .ic {
    width: var(--control-s);
    height: var(--control-s);
    display: grid;
    place-items: center;
    border-radius: var(--radius-m);
    background: color-mix(in oklab, var(--tone) 20%, transparent);
    color: var(--tone);
    font-size: var(--size-caption);
  }
  .what {
    display: flex;
    align-items: center;
    gap: var(--space-s);
    min-width: 0;
    white-space: nowrap;
    overflow: hidden;
  }
  .verb {
    color: var(--muted);
    font-size: var(--size-body);
  }
  .keycaps {
    display: inline-flex;
    gap: var(--space-xxs);
  }
  kbd {
    min-width: var(--space-m);
    padding: 0 var(--space-s);
    border: 1px solid var(--line);
    border-bottom-width: 2px;
    border-radius: var(--radius-s);
    background: var(--raised);
    color: var(--text);
    font: 700 var(--size-caption) / 1.5 var(--font-strong);
    text-align: center;
    text-transform: capitalize;
  }
  .thumb {
    height: var(--space-xl);
    max-width: calc(2 * var(--control-l));
    border-radius: var(--radius-s);
    object-fit: contain;
  }
  .tgt {
    font: 600 var(--size-body) / 1.3 var(--mono);
    color: var(--text);
    overflow: hidden;
    text-overflow: ellipsis;
  }
  .what small,
  .note {
    color: var(--faint);
    font-size: var(--size-caption);
  }
  .tape {
    display: inline-grid;
    grid-template-columns: calc(3 * var(--control-l)) calc(8 * var(--control-l));
    align-items: center;
    gap: var(--space-s);
  }
  .tape svg {
    width: 100%;
    height: var(--control-l);
    border-radius: var(--radius-s);
    background: var(--raised);
  }
  .tape polyline {
    fill: none;
    stroke: var(--accent);
    stroke-width: 1;
    vector-effect: non-scaling-stroke;
  }
  .marks {
    position: relative;
    height: var(--control-s);
    border-radius: var(--radius-s);
    background: var(--raised);
  }
  .marks i {
    position: absolute;
    top: var(--space-xs);
    bottom: var(--space-xs);
    width: 1px;
    background: var(--accent-2);
  }
  .marks i[data-kind="click"] {
    background: var(--accent);
  }
  .marks i[data-kind="wheel"] {
    background: var(--warn);
  }
  .dur {
    display: inline-flex;
    align-items: center;
    gap: var(--space-s);
    width: calc(5 * var(--control-m));
    font: 600 var(--size-caption) / 1 var(--mono);
  }
  .dur i {
    display: block;
    height: var(--space-xs);
    border-radius: var(--radius-pill);
    background: linear-gradient(90deg, var(--faint), var(--muted));
  }
  code {
    color: var(--muted);
    font: var(--size-caption) / 1.4 var(--mono);
    white-space: pre;
  }
  .callchip {
    display: inline-flex;
    align-items: center;
    gap: var(--space-s);
    padding: var(--space-xxs) var(--space-xs) var(--space-xxs) var(--space-m);
    border-radius: var(--radius-pill);
    border: 1px solid color-mix(in oklab, var(--slot-bot) 40%, transparent);
    background: linear-gradient(90deg, color-mix(in oklab, var(--slot-bot) 18%, transparent), color-mix(in oklab, var(--accent-2) 10%, transparent));
    color: var(--slot-bot);
    font: 700 var(--size-caption) / 1.4 var(--font-strong);
  }
  .mini {
    padding: 0 var(--space-s);
    border: 0;
    border-radius: var(--radius-pill);
    background: var(--raised-hover);
    color: var(--text);
    font: 600 var(--size-caption) / 1.6 var(--font-strong);
    cursor: pointer;
  }
  .bp {
    width: var(--space-m);
    height: var(--space-m);
    padding: 0;
    border: 1px solid transparent;
    border-radius: 50%;
    background: none;
    cursor: pointer;
  }
  .row:hover .bp {
    border-color: var(--faint);
  }
  .bp.set {
    background: var(--danger);
    border-color: var(--danger);
    box-shadow: 0 0 var(--space-s) var(--danger);
  }
  .between {
    position: absolute;
    left: calc(2 * var(--control-m));
    bottom: calc(-1 * var(--space-s));
    z-index: 2;
    width: var(--space-l);
    height: var(--space-l);
    padding: 0;
    border: 0;
    border-radius: 50%;
    background: var(--accent);
    color: var(--on-accent);
    font: 800 var(--size-caption) / 1 var(--font-strong);
    cursor: pointer;
    opacity: 0;
    transition: opacity var(--duration-fast) var(--curve-easy-ease);
  }
  .row:hover .between {
    opacity: 1;
  }
  .adder {
    display: flex;
    flex-wrap: wrap;
    gap: var(--space-xs);
    margin: var(--space-xs) 0 var(--space-s) calc(var(--depth, 0) * var(--space-xl) + 2 * var(--control-m));
    animation: slide var(--duration-normal) var(--curve-decelerate);
  }
  .settings {
    display: flex;
    flex-wrap: wrap;
    gap: var(--space-m);
    align-items: end;
    margin: var(--space-xs) 0 var(--space-s) calc(2 * var(--control-m));
    padding: var(--space-m);
    border-radius: var(--radius-l);
    background: linear-gradient(180deg, color-mix(in oklab, var(--accent) 8%, transparent), var(--raised));
    border: 1px solid color-mix(in oklab, var(--accent) 25%, transparent);
    font-size: var(--size-caption);
    animation: slide var(--duration-normal) var(--curve-decelerate);
  }
  .settings label {
    display: grid;
    gap: var(--space-xxs);
    color: var(--muted);
  }
  .settings label.wide {
    flex: 1 1 100%;
  }
  .settings input,
  .settings select,
  .settings textarea {
    padding: var(--space-s) var(--space-m);
    border: 1px solid var(--line);
    border-radius: var(--radius-m);
    background: color-mix(in oklab, var(--bg) 50%, transparent);
    color: var(--text);
    font: inherit;
    font-size: var(--size-body);
  }
  .settings textarea {
    font-family: var(--mono);
  }
  .peek {
    margin: var(--space-xs) 0 var(--space-s) calc(var(--depth, 0) * var(--space-xl) + 2 * var(--control-m));
    padding: var(--space-s);
    border-radius: var(--radius-l);
    border: 1px solid color-mix(in oklab, var(--slot-bot) 30%, transparent);
    background: color-mix(in oklab, var(--slot-bot) 6%, transparent);
    animation: slide var(--duration-normal) var(--curve-decelerate);
  }
  .peekhead {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 0 var(--space-s) var(--space-xs);
    color: var(--muted);
    font-size: var(--size-caption);
  }
  .peekhead b {
    color: var(--slot-bot);
  }
  .block {
    margin-left: calc(var(--depth, 0) * var(--space-xl) + var(--space-xl));
    padding-left: var(--space-s);
    border-left: 2px solid color-mix(in oklab, var(--ok) 45%, transparent);
  }
  .block.loop {
    border-left-color: color-mix(in oklab, var(--warn) 50%, transparent);
  }
  .empty-add {
    margin: var(--space-xs) var(--space-m);
  }
  .savebar {
    position: fixed;
    left: 50%;
    bottom: var(--space-xl);
    translate: -50% 0;
    z-index: 20;
    display: flex;
    align-items: center;
    gap: var(--space-m);
    padding: var(--space-s) var(--space-s) var(--space-s) var(--space-l);
    border-radius: var(--radius-pill);
    background: var(--glass-strong);
    border: 1px solid var(--line);
    box-shadow: var(--shadow);
    font: 600 var(--size-body) / 1 var(--font-strong);
    animation: slide var(--duration-normal) var(--curve-decelerate);
  }
  @keyframes slide {
    from {
      opacity: 0;
      transform: translateY(calc(-1 * var(--space-xs)));
    }
  }
  @keyframes flash {
    50% {
      background: color-mix(in oklab, var(--danger) 25%, transparent);
    }
  }
</style>
