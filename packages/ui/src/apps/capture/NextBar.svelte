<!-- Between guide items: a small bar at the top of the screen naming the next picture, while the game is free to
     use. Open that screen, then press Ctrl+Alt+C or Freeze. Decision 0013, round 7. -->
<script lang="ts">
  import { on, request } from "$lib/api";

  interface ItemInfo {
    name: string;
    kind: string;
    say: string;
    screen: string;
  }

  let next: ItemInfo | null = $state(null);
  let left = $state(0);

  async function load(): Promise<void> {
    const found = await request("capture.session").catch(() => null);
    if (!found) return;
    left = found.items.length;
    next = found.items[0] ?? null;
  }

  $effect(() => {
    load();
    const stop = on("capture.waiting", () => load());
    return stop;
  });
</script>

<div class="bar">
  <div class="pill">
    <span class="dot" aria-hidden="true"></span>
    <span class="text">
      <b>Next: {next?.name ?? "…"}</b>
      <small>{next?.screen ? `Open ${next.screen} in the game, then` : "Then"} press <kbd>Ctrl</kbd>+<kbd>Alt</kbd>+<kbd>C</kbd> · {left} left</small>
    </span>
    <button class="go" onclick={() => request("capture.refreeze")}>▣ Freeze</button>
    <button class="stop" aria-label="Stop capturing" title="Stop capturing" onclick={() => request("capture.close")}>✕</button>
  </div>
</div>

<style>
  :global(html),
  :global(body) {
    margin: 0;
    background: transparent;
    overflow: hidden;
  }
  .bar {
    display: grid;
    place-items: center;
    height: 100vh;
    font-family: var(--font);
    color: var(--text);
  }
  .pill {
    display: flex;
    align-items: center;
    gap: var(--space-m);
    padding: var(--space-s) var(--space-s) var(--space-s) var(--space-l);
    border-radius: var(--radius-pill);
    background: var(--glass-strong);
    border: 1px solid var(--line);
    box-shadow: var(--shadow);
    animation: drop var(--duration-normal) var(--curve-decelerate);
  }
  .dot {
    width: var(--space-s);
    height: var(--space-s);
    border-radius: 50%;
    background: var(--warn);
  }
  .text {
    display: grid;
    font-size: var(--size-caption);
  }
  .text b {
    font: 700 var(--size-body) / 1.3 var(--mono);
  }
  small {
    color: var(--muted);
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
  .go,
  .stop {
    height: var(--control-m);
    border: 0;
    border-radius: var(--radius-pill);
    font: 700 var(--size-caption) / 1 var(--font-strong);
    cursor: pointer;
  }
  .go {
    padding: 0 var(--space-l);
    background: var(--accent);
    color: var(--on-accent);
  }
  .stop {
    width: var(--control-m);
    background: var(--raised);
    color: var(--muted);
  }
  @keyframes drop {
    from {
      opacity: 0;
      transform: translateY(calc(-1 * var(--space-m)));
    }
  }
</style>
