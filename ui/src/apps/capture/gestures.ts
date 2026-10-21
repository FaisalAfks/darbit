// Mouse gestures on the frozen screen → actions. The [mouse] scope of keymap.toml names them.
// See docs/tasks/T09-capture-overlay.md step 3.

export type Gesture =
  | { do: "select"; x: number; y: number; again: boolean } // click; again = same spot as the last click
  | { do: "draw"; kind: "current" | "region"; from: [number, number]; to: [number, number] }
  | { do: "point"; x: number; y: number } // ctrl+click
  | { do: "menu"; x: number; y: number }; // right-click

const CLICK = 4; // a press and release closer than this is a click, not a drag

/** What a finished press-and-release means. */
export function gesture(down: PointerEvent, up: PointerEvent, last?: [number, number]): Gesture {
  const moved = Math.abs(up.clientX - down.clientX) >= CLICK || Math.abs(up.clientY - down.clientY) >= CLICK;
  if (down.button === 2) return { do: "menu", x: up.clientX, y: up.clientY };
  if (!moved && down.ctrlKey) return { do: "point", x: up.clientX, y: up.clientY };
  if (!moved) {
    const again = !!last && Math.abs(last[0] - up.clientX) <= CLICK && Math.abs(last[1] - up.clientY) <= CLICK;
    return { do: "select", x: up.clientX, y: up.clientY, again };
  }
  return {
    do: "draw",
    kind: down.shiftKey ? "region" : "current",
    from: [down.clientX, down.clientY],
    to: [up.clientX, up.clientY],
  };
}
