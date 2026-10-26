// Tooltips from one layer at the top of the page, so no panel can clip them (design system, review rules).
// Use on any element: <button use:tip={{ label: "Save", keys: "enter" }}>. Shows on hover and on keyboard
// focus, above the element, or below it near the top of the window; always inside the window.
import "./tooltip.css";
import { keyNames } from "./keys";

export interface TipOptions {
  label: string;
  keys?: string; // "ctrl+alt+c"
}

let layer: HTMLDivElement | null = null;

function getLayer(): HTMLDivElement {
  if (!layer) {
    layer = document.createElement("div");
    layer.className = "darbit-tip";
    layer.setAttribute("role", "tooltip");
    document.body.append(layer);
  }
  return layer;
}

function fill(target: HTMLDivElement, options: TipOptions): void {
  target.replaceChildren(document.createTextNode(options.label));
  if (!options.keys) return;
  for (const name of keyNames(options.keys)) {
    const cap = document.createElement("kbd");
    cap.textContent = name;
    target.append(cap);
  }
}

function place(target: HTMLDivElement, anchor: HTMLElement): void {
  const margin = 8;
  const box = anchor.getBoundingClientRect();
  const size = target.getBoundingClientRect();
  let top = box.top - size.height - margin;
  if (top < margin) top = box.bottom + margin; // too close to the top: below instead
  let left = box.left + box.width / 2 - size.width / 2;
  left = Math.max(margin, Math.min(left, window.innerWidth - size.width - margin));
  target.style.translate = `${Math.round(left)}px ${Math.round(top)}px`;
}

export function tip(node: HTMLElement, options: TipOptions) {
  let current = options;

  function show(): void {
    const target = getLayer();
    fill(target, current);
    target.classList.add("on");
    place(target, node);
  }

  function hide(): void {
    getLayer().classList.remove("on");
  }

  node.addEventListener("pointerenter", show);
  node.addEventListener("pointerleave", hide);
  node.addEventListener("focus", show);
  node.addEventListener("blur", hide);
  node.addEventListener("click", hide);

  return {
    update(next: TipOptions) {
      current = next;
    },
    destroy() {
      hide();
      node.removeEventListener("pointerenter", show);
      node.removeEventListener("pointerleave", hide);
      node.removeEventListener("focus", show);
      node.removeEventListener("blur", hide);
      node.removeEventListener("click", hide);
    },
  };
}
