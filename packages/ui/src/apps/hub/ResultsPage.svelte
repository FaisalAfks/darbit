<!-- The Results page: is the bot getting what I want, and what needs fixing? A day list on the left; the chosen
     day as a sentence, its problems, a table of gains and progress, and a whole-day timeline that zooms and
     drags. Filled from the run report (server/results.py). Decision 0013, round 5d. -->
<script lang="ts">
  import { request } from "$lib/api";
  import { toast } from "$lib/toasts.svelte";
  import { clock, duration } from "./time";

  interface DayEntry {
    day: string;
    lead: { name: string; amount: number; icon: string | null } | null;
    seconds: number;
    problems: number;
  }
  interface Gain {
    name: string;
    today: number;
    total: number | null;
    icon: string | null;
    week: number[];
  }
  interface Problem {
    step: string;
    path: string;
    reason: string;
    count: number;
    times: string[];
  }
  interface Lane {
    name: string;
    blocks: { start: number | null; end: number | null; state: string }[];
  }
  interface Day {
    day: string;
    start: number | null;
    end: number | null;
    week_days: string[];
    gains: Gain[];
    progress: { label: string; done: number; total: number }[];
    finished: { done: number; total: number };
    lost_seconds: number;
    problems: Problem[];
    lanes: Lane[];
  }

  let { path, onretake }: { path: string; onretake: (step: string) => void } = $props();

  const ZOOMS = [1, 2, 4, 8, 16];
  const ZOOM_NAMES = ["Whole day", "12 h", "6 h", "3 h", "90 min"];
  const DAY_SECONDS = 24 * 3600;
  const TONES = ["var(--accent)", "var(--warn)", "var(--accent-2)", "var(--ok)", "var(--kind-region)"];

  let days: DayEntry[] = $state([]);
  let chosen = $state("");
  let page = $state<Day | null>(null);
  let loaded = $state(false);
  let zoom = $state(0);
  let view: HTMLElement | undefined = $state();
  let viewLeft = $state(0);
  let viewShare = $state(1);

  const today = new Date().toISOString().slice(0, 10);
  const leadName = $derived(days.find((entry) => entry.lead)?.lead?.name ?? "");
  const weekLead = $derived(sumLead(days.slice(0, 7)));
  const lanes = $derived(page?.lanes ?? []);
  const hours = $derived(hourMarks(zoom));

  function sumLead(entries: DayEntry[]): number {
    let total = 0;
    for (const entry of entries) if (entry.lead && entry.lead.name === leadName) total += entry.lead.amount;
    return total;
  }

  function hourMarks(level: number): number[] {
    const step = ZOOMS[level] >= 8 ? 0.5 : ZOOMS[level] >= 2 ? 1 : 2;
    const marks: number[] = [];
    for (let hour = 0; hour < 24; hour += step) marks.push(hour);
    return marks;
  }

  function signed(amount: number): string {
    const text = Math.abs(amount).toLocaleString("en").replace(/,/g, " ");
    return `${amount < 0 ? "−" : "+"}${text}`;
  }

  function plain(amount: number | null): string {
    if (amount === null || amount === undefined) return "";
    return amount.toLocaleString("en").replace(/,/g, " ");
  }

  function dayName(day: string): string {
    if (day === today) return "Today";
    return new Date(day + "T12:00:00").toLocaleDateString("en-GB", { weekday: "long" });
  }

  function longDay(day: string): string {
    return new Date(day + "T12:00:00").toLocaleDateString("en-GB", { weekday: "long", day: "numeric", month: "short" });
  }

  function clockOf(seconds: number | null): string {
    if (seconds === null) return "";
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    return `${String(hours).padStart(2, "0")}:${String(minutes).padStart(2, "0")}`;
  }

  function sentenceParts(day: Day): { ran: string; gains: Gain[]; share: number | null; lost: string } {
    const ran = day.start !== null && day.end !== null ? duration(day.end - day.start) : "";
    const share = day.finished.total ? Math.round((day.finished.done / day.finished.total) * 100) : null;
    return { ran, gains: day.gains.slice(0, 2), share, lost: day.lost_seconds ? duration(day.lost_seconds) : "" };
  }

  async function loadDays(): Promise<void> {
    days = await request<DayEntry[]>("results.days", { path });
    if (!chosen && days.length) chosen = days[0].day;
    loaded = true;
  }

  async function loadDay(): Promise<void> {
    if (!chosen) return;
    page = await request<Day>("results.day", { path, day: chosen });
  }

  function setZoom(next: number): void {
    if (!view) return;
    const centre = (view.scrollLeft + view.clientWidth / 2) / view.scrollWidth;
    zoom = Math.max(0, Math.min(ZOOMS.length - 1, next));
    requestAnimationFrame(() => {
      if (!view) return;
      view.scrollLeft = centre * view.scrollWidth - view.clientWidth / 2;
      follow();
    });
  }

  function follow(): void {
    if (!view) return;
    viewLeft = view.scrollLeft / view.scrollWidth;
    viewShare = view.clientWidth / view.scrollWidth;
  }

  function wheel(event: WheelEvent): void {
    if (!event.ctrlKey) return;
    event.preventDefault();
    setZoom(zoom + (event.deltaY < 0 ? 1 : -1));
  }

  let drag: { x: number; left: number; mini: boolean } | null = null;
  function grab(event: PointerEvent, mini: boolean): void {
    if (!view) return;
    if (mini) {
      const box = (event.currentTarget as HTMLElement).getBoundingClientRect();
      view.scrollLeft = ((event.clientX - box.left) / box.width) * view.scrollWidth - view.clientWidth / 2;
    }
    drag = { x: event.clientX, left: view.scrollLeft, mini };
    (event.currentTarget as HTMLElement).setPointerCapture(event.pointerId);
    follow();
  }
  function move(event: PointerEvent, width: number): void {
    if (!drag || !view) return;
    const moved = event.clientX - drag.x;
    view.scrollLeft = drag.mini ? drag.left + (moved * view.scrollWidth) / width : drag.left - moved;
    follow();
  }

  function left(seconds: number | null): string {
    return `${((seconds ?? 0) / DAY_SECONDS) * 100}%`;
  }
  function width(start: number | null, end: number | null): string {
    const from = start ?? 0;
    const to = end ?? from + 60;
    return `max(3px, ${((to - from) / DAY_SECONDS) * 100}%)`;
  }

  $effect(() => {
    path;
    chosen = "";
    page = null;
    loadDays().catch((error: Error) => toast(error.message));
  });

  $effect(() => {
    chosen;
    loadDay().catch((error: Error) => toast(error.message));
  });
</script>

{#if loaded && !days.length}
  <p class="empty">No runs yet. When the bot runs, each day shows up here with what it got.</p>
{:else if loaded}
  <div class="results">
    <nav class="days" aria-label="Days">
      {#if leadName}<div class="week">This week <b>{signed(weekLead)} {leadName.toLowerCase()}</b></div>{/if}
      {#each days as entry (entry.day)}
        <button class="day" class:on={entry.day === chosen} onclick={() => (chosen = entry.day)}>
          <b>{dayName(entry.day)}{#if entry.problems}<i class="bad-dot" aria-label="had problems"></i>{/if}</b>
          {#if entry.lead}<span class="gain">{signed(entry.lead.amount)}</span>{:else}<span></span>{/if}
          <small>{entry.seconds ? duration(entry.seconds) : "no run time"}{entry.problems ? ` · ${entry.problems} problem${entry.problems > 1 ? "s" : ""}` : ""}</small>
        </button>
      {/each}
    </nav>

    {#if page}
      {@const parts = sentenceParts(page)}
      <section class="story">
        <div class="summary panel">
          <div class="head"><h2>{longDay(page.day)}</h2>{#if page.start !== null}<span class="muted">{clockOf(page.start)} – {clockOf(page.end)}</span>{/if}</div>
          <p class="sentence">
            {#if parts.ran}Ran <b>{parts.ran}</b>{:else}Nothing ran{/if}{#if parts.gains.length}{" "}and got{#each parts.gains as gain, index (gain.name)}{index ? " and" : ""} <span class="plus">{signed(gain.today)} {gain.name.toLowerCase()}</span>{/each}{/if}.
            {#if parts.share !== null}It finished <b>{parts.share}%</b> of its rounds{#if parts.lost}{" "}and lost about <b>{parts.lost}</b> to problems{/if}.{/if}
          </p>
          {#each page.problems.slice(0, 3) as problem (problem.step + problem.reason)}
            <div class="problem">
              <span class="mark" aria-hidden="true">!</span>
              <span><b>{problem.step}: {problem.reason}{problem.count > 1 ? `, ${problem.count} times` : ""}</b><small>{problem.times.map(clock).join(", ")}</small></span>
              <button class="fix" onclick={() => onretake(problem.step)}>▣ Retake</button>
            </div>
          {/each}
        </div>

        {#if page.gains.length || page.progress.length}
          <div class="ledger panel">
            <h3><span>What it got</span><span>today · the week · total</span></h3>
            <table>
              <tbody>
                {#each page.gains as gain, index (gain.name)}
                  {@const most = Math.max(1, ...gain.week)}
                  <tr style:--tone={TONES[index % TONES.length]}>
                    <td><span class="name"><span class="icon">{gain.icon ?? "◆"}</span>{gain.name}</span></td>
                    <td class="right"><span class="plus">{signed(gain.today)}</span></td>
                    <td><span class="spark">{#each gain.week as amount, at (at)}<i class:on={at === gain.week.length - 1} style:height="{Math.max(6, (amount / most) * 100)}%"></i>{/each}</span></td>
                    <td class="right muted">{plain(gain.total)}</td>
                  </tr>
                {/each}
                {#each page.progress as item (item.label)}
                  <tr style:--tone="var(--ok)">
                    <td><span class="name"><span class="icon">✓</span>{item.label}</span></td>
                    <td></td>
                    <td><span class="bar"><i style:width="{Math.min(100, (item.done / item.total) * 100)}%"></i></span></td>
                    <td class="right muted">{plain(item.done)} / {plain(item.total)}</td>
                  </tr>
                {/each}
              </tbody>
            </table>
          </div>
        {/if}

        {#if lanes.length}
          <div class="timeline panel">
            <div class="tl-head">
              <h3><span>Timeline</span></h3>
              <span class="grow"></span>
              <div class="zoom" role="group" aria-label="Zoom">
                <button aria-label="Zoom out" disabled={zoom === 0} onclick={() => setZoom(zoom - 1)}>−</button>
                <span>{ZOOM_NAMES[zoom]}</span>
                <button aria-label="Zoom in" disabled={zoom === ZOOMS.length - 1} onclick={() => setZoom(zoom + 1)}>+</button>
              </div>
            </div>
            <div class="tl-body">
              <div class="names">
                <span class="spacer"></span>
                {#each lanes as lane (lane.name)}<span class="lane-name">{lane.name}</span>{/each}
              </div>
              <div
                class="view"
                bind:this={view}
                onscroll={follow}
                onwheel={wheel}
                onpointerdown={(event) => grab(event, false)}
                onpointermove={(event) => move(event, 0)}
                onpointerup={() => (drag = null)}
                role="presentation"
              >
                <div class="canvas" style:width="{ZOOMS[zoom] * 100}%">
                  <div class="hours">{#each hours as hour (hour)}<span style:left="{(hour / 24) * 100}%">{String(Math.floor(hour)).padStart(2, "0")}:{hour % 1 ? "30" : "00"}</span>{/each}</div>
                  {#each lanes as lane (lane.name)}
                    <div class="track">
                      {#each lane.blocks as block, at (at)}
                        <i class="block" data-state={block.state} style:left={left(block.start)} style:width={width(block.start, block.end)} title="{lane.name} · {clockOf(block.start)} · {block.state}"></i>
                      {/each}
                    </div>
                  {/each}
                </div>
              </div>
            </div>
            <div
              class="mini"
              onpointerdown={(event) => grab(event, true)}
              onpointermove={(event) => move(event, (event.currentTarget as HTMLElement).clientWidth)}
              onpointerup={() => (drag = null)}
              role="presentation"
            >
              {#each lanes as lane (lane.name)}{#each lane.blocks as block, at (at)}<i data-state={block.state} style:left={left(block.start)} style:width={width(block.start, block.end)}></i>{/each}{/each}
              <span class="frame" style:left="{viewLeft * 100}%" style:width="{viewShare * 100}%"></span>
            </div>
          </div>
        {/if}
      </section>
    {/if}
  </div>
{/if}

<style>
  .results {
    display: grid;
    grid-template-columns: calc(7 * var(--control-m)) 1fr;
    gap: var(--space-l);
    align-items: start;
  }
  .panel {
    border-radius: var(--radius-xl);
    background: var(--glass);
    border: 1px solid var(--line);
  }
  .days {
    display: grid;
    gap: var(--space-xxs);
    padding: var(--space-m);
    border-radius: var(--radius-xl);
    background: var(--glass);
    border: 1px solid var(--line);
    position: sticky;
    top: var(--space-l);
    max-height: calc(100vh - 6 * var(--space-xl));
    overflow: auto;
  }
  .week {
    padding: var(--space-s) var(--space-m) var(--space-m);
    border-bottom: 1px solid var(--line);
    margin-bottom: var(--space-xs);
    color: var(--muted);
    font-size: var(--size-caption);
  }
  .week b {
    color: var(--ok);
  }
  .day {
    display: grid;
    grid-template-columns: 1fr auto;
    gap: 0 var(--space-s);
    padding: var(--space-s) var(--space-m);
    border: 0;
    border-radius: var(--radius-m);
    background: none;
    color: var(--text);
    font: inherit;
    text-align: left;
    cursor: pointer;
    transition: background var(--duration-fast) var(--curve-easy-ease);
  }
  .day:hover {
    background: var(--raised);
  }
  .day.on {
    background: color-mix(in oklab, var(--accent) 14%, transparent);
    box-shadow: inset 2px 0 0 var(--accent);
  }
  .day b {
    font: 650 var(--size-body) / var(--line-body) var(--font-strong);
    display: flex;
    align-items: center;
    gap: var(--space-s);
  }
  .day small {
    grid-column: 1 / -1;
    color: var(--muted);
    font-size: var(--size-caption);
  }
  .gain {
    color: var(--ok);
    font: 700 var(--size-caption) / var(--line-body) var(--font-strong);
  }
  .bad-dot {
    width: var(--space-s);
    height: var(--space-s);
    border-radius: 50%;
    background: var(--danger);
  }
  .story {
    display: grid;
    gap: var(--space-m);
    min-width: 0;
  }
  .summary {
    display: grid;
    gap: var(--space-m);
    padding: var(--space-l) var(--space-xl);
  }
  .head {
    display: flex;
    align-items: baseline;
    gap: var(--space-m);
  }
  h2 {
    margin: 0;
    font: 700 var(--size-title3) / var(--line-title3) var(--font-strong);
  }
  .muted {
    color: var(--muted);
    font-size: var(--size-caption);
  }
  .sentence {
    margin: 0;
    color: var(--muted);
    font-size: var(--size-subtitle);
    line-height: var(--line-subtitle);
  }
  .sentence b {
    color: var(--text);
  }
  .plus {
    color: var(--ok);
    font-weight: 700;
  }
  .problem {
    display: grid;
    grid-template-columns: auto 1fr auto;
    gap: var(--space-m);
    align-items: center;
    padding: var(--space-m);
    border-radius: var(--radius-l);
    background: linear-gradient(90deg, color-mix(in oklab, var(--danger) 14%, transparent), color-mix(in oklab, var(--danger) 4%, transparent));
    border: 1px solid color-mix(in oklab, var(--danger) 30%, transparent);
    animation: rise var(--duration-normal) var(--curve-decelerate);
  }
  .problem > span:nth-child(2) {
    display: grid;
  }
  .problem small {
    color: var(--muted);
    font-size: var(--size-caption);
  }
  .mark {
    width: var(--control-m);
    height: var(--control-m);
    display: grid;
    place-items: center;
    border-radius: 50%;
    background: color-mix(in oklab, var(--danger) 22%, transparent);
    color: var(--danger);
    font-weight: 800;
  }
  .fix {
    height: var(--control-m);
    padding: 0 var(--space-l);
    border: 0;
    border-radius: var(--radius-pill);
    background: var(--accent);
    color: var(--on-accent);
    font: 650 var(--size-caption) / 1 var(--font-strong);
    cursor: pointer;
  }
  .ledger,
  .timeline {
    padding: var(--space-m) var(--space-l) var(--space-l);
  }
  h3 {
    margin: var(--space-s) 0;
    display: flex;
    justify-content: space-between;
    font: 700 var(--size-caption) / 1 var(--font-strong);
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: var(--muted);
  }
  table {
    width: 100%;
    border-collapse: collapse;
  }
  td {
    padding: var(--space-s) var(--space-s);
    border-top: 1px solid var(--line);
    vertical-align: middle;
  }
  .right {
    text-align: right;
  }
  .name {
    display: flex;
    align-items: center;
    gap: var(--space-m);
    font-weight: 600;
  }
  .icon {
    width: var(--control-s);
    height: var(--control-s);
    display: grid;
    place-items: center;
    border-radius: var(--radius-m);
    background: color-mix(in oklab, var(--tone) 22%, transparent);
    color: var(--tone);
    font-size: var(--size-caption);
  }
  .spark {
    display: flex;
    align-items: end;
    gap: var(--space-xxs);
    height: var(--space-xl);
    width: calc(4 * var(--control-m));
  }
  .spark i {
    flex: 1;
    border-radius: var(--radius-s) var(--radius-s) 0 0;
    background: color-mix(in oklab, var(--tone) 55%, transparent);
  }
  .spark i.on {
    background: var(--tone);
  }
  .bar {
    display: block;
    width: calc(4 * var(--control-m));
    height: var(--space-s);
    border-radius: var(--radius-pill);
    background: var(--raised);
    overflow: hidden;
  }
  .bar i {
    display: block;
    height: 100%;
    background: linear-gradient(90deg, var(--accent), var(--accent-2));
  }
  .tl-head {
    display: flex;
    align-items: center;
    gap: var(--space-m);
  }
  .grow {
    flex: 1;
  }
  .zoom {
    display: flex;
    align-items: center;
    gap: var(--space-xxs);
    padding: var(--space-xxs);
    border-radius: var(--radius-pill);
    background: var(--raised);
  }
  .zoom button {
    width: var(--control-s);
    height: var(--control-s);
    border: 0;
    border-radius: 50%;
    background: none;
    color: var(--text);
    font: 700 var(--size-body) / 1 var(--font-strong);
    cursor: pointer;
  }
  .zoom button:hover:not(:disabled) {
    background: var(--raised-hover);
  }
  .zoom button:disabled {
    opacity: 0.35;
  }
  .zoom span {
    min-width: calc(3 * var(--control-m));
    text-align: center;
    color: var(--muted);
    font: 600 var(--size-caption) / 1 var(--font-strong);
  }
  .tl-body {
    display: grid;
    grid-template-columns: auto 1fr;
    gap: var(--space-m);
  }
  .names {
    display: grid;
    grid-auto-rows: var(--control-s);
    gap: var(--space-xs);
    font-size: var(--size-caption);
    align-items: center;
  }
  .spacer {
    height: var(--space-l);
  }
  .names .spacer {
    height: auto;
  }
  .view {
    overflow: hidden;
    cursor: grab;
    border-radius: var(--radius-m);
    user-select: none;
  }
  .view:active {
    cursor: grabbing;
  }
  .canvas {
    display: grid;
    grid-auto-rows: var(--control-s);
    gap: var(--space-xs);
    transition: width var(--duration-normal) var(--curve-decelerate);
  }
  .hours {
    position: relative;
    font-size: var(--size-caption);
    color: var(--faint);
  }
  .hours span {
    position: absolute;
    top: var(--space-xs);
    translate: calc(-1 * var(--space-s)) 0;
  }
  .track {
    position: relative;
    border-radius: var(--radius-s);
    background: var(--raised);
  }
  .block {
    position: absolute;
    top: var(--space-xs);
    bottom: var(--space-xs);
    border-radius: var(--radius-s);
    background: color-mix(in oklab, var(--accent) 60%, transparent);
  }
  .block[data-state="ok"] {
    background: color-mix(in oklab, var(--ok) 60%, transparent);
  }
  .block[data-state="failed"] {
    background: var(--danger);
  }
  .mini {
    position: relative;
    height: var(--space-l);
    margin-top: var(--space-s);
    border-radius: var(--radius-m);
    background: var(--raised);
    overflow: hidden;
    cursor: pointer;
  }
  .mini i {
    position: absolute;
    top: var(--space-s-nudge);
    bottom: var(--space-s-nudge);
    border-radius: var(--radius-s);
    background: color-mix(in oklab, var(--accent) 50%, transparent);
  }
  .mini i[data-state="failed"] {
    background: var(--danger);
  }
  .frame {
    position: absolute;
    top: 0;
    bottom: 0;
    border-radius: var(--radius-m);
    border: 2px solid var(--text);
    background: color-mix(in oklab, var(--text) 8%, transparent);
  }
  .empty {
    color: var(--muted);
    margin: var(--space-xxl) auto;
    text-align: center;
  }
  @keyframes rise {
    from {
      opacity: 0;
      transform: translateY(var(--space-xs));
    }
  }
</style>
