// WCAG 2.2 contrast for every theme: text on each surface (4.5:1; 3:1 for faint, secondary text is allowed to
// be quieter only down to 3:1), text on accent and status colours (4.5:1), and controls and borders that
// must be seen (3:1, non-text contrast). See of https://www.w3.org/TR/WCAG22/#contrast-minimum and #non-text-contrast.
// Translucent surfaces are mixed over the theme's background first, as they show on screen.
import { readFileSync } from "node:fs";

type Rgba = [number, number, number, number];

const themes = readFileSync(new URL("../src/lib/tokens/themes.css", import.meta.url), "utf8");

function parse(value: string): Rgba | null {
  const text = value.trim();
  const hex = text.match(/^#([0-9a-f]{3}|[0-9a-f]{6})$/i);
  if (hex) {
    let digits = hex[1];
    if (digits.length === 3) digits = digits[0] + digits[0] + digits[1] + digits[1] + digits[2] + digits[2];
    return [parseInt(digits.slice(0, 2), 16), parseInt(digits.slice(2, 4), 16), parseInt(digits.slice(4, 6), 16), 1];
  }
  const rgb = text.match(/^rgb\(\s*(\d+)\s+(\d+)\s+(\d+)\s*(?:\/\s*([\d.]+))?\s*\)$/);
  if (rgb) return [Number(rgb[1]), Number(rgb[2]), Number(rgb[3]), rgb[4] === undefined ? 1 : Number(rgb[4])];
  return null;
}

function over(top: Rgba, below: Rgba): Rgba {
  const a = top[3];
  return [top[0] * a + below[0] * (1 - a), top[1] * a + below[1] * (1 - a), top[2] * a + below[2] * (1 - a), 1];
}

function luminance(colour: Rgba): number {
  const channels = [colour[0], colour[1], colour[2]].map((value) => {
    const s = value / 255;
    return s <= 0.04045 ? s / 12.92 : ((s + 0.055) / 1.055) ** 2.4;
  });
  return 0.2126 * channels[0] + 0.7152 * channels[1] + 0.0722 * channels[2];
}

function ratio(a: Rgba, b: Rgba): number {
  const la = luminance(a);
  const lb = luminance(b);
  return (Math.max(la, lb) + 0.05) / (Math.min(la, lb) + 0.05);
}

// [foreground token, background token, needed ratio, what it is]
const PAIRS: [string, string, number, string][] = [];
for (const surface of ["--bg", "--glass", "--glass-strong", "--raised-on-glass"]) {
  PAIRS.push(["--text", surface, 4.5, "text"]);
  PAIRS.push(["--muted", surface, 4.5, "secondary text"]);
  PAIRS.push(["--faint", surface, 3, "hint text and step numbers"]);
  PAIRS.push(["--slot-tool", surface, 4.5, "darbit's text"]);
  PAIRS.push(["--slot-bot", surface, 4.5, "a bot's text"]);
  PAIRS.push(["--accent", surface, 3, "accent as an indicator"]);
  for (const status of ["--ok", "--warn", "--danger", "--info"]) PAIRS.push([status, surface, 4.5, "status text"]);
  for (const kind of ["--kind-image", "--kind-region", "--kind-point"]) PAIRS.push([kind, surface, 3, "target kind outline"]);
}
PAIRS.push(["--on-accent", "--accent", 4.5, "text on the accent"]);
for (const status of ["--ok", "--warn", "--danger", "--info"]) PAIRS.push(["--on-status", status, 4.5, "text on a status badge"]);

const blocks = [...themes.matchAll(/((?::root,\s*)?\[data-theme="([a-z-]+)"\])\s*\{([^}]*)\}/g)];
let failures = 0;
for (const block of blocks) {
  const name = block[2];
  const tokens = new Map<string, string>();
  for (const match of block[3].matchAll(/(--[a-z0-9-]+)\s*:\s*([^;]+);/g)) tokens.set(match[1], match[2]);
  const background = parse(tokens.get("--bg") ?? "");
  if (!background) continue;

  function solid(token: string): Rgba | null {
    if (token === "--raised-on-glass") {
      const glass = solid("--glass");
      const raised = parse(tokens.get("--raised") ?? "");
      return glass && raised ? over(raised, glass) : null;
    }
    const value = parse(tokens.get(token) ?? "");
    return value ? over(value, background!) : null;
  }

  const problems: string[] = [];
  for (const [front, back, needed, what] of PAIRS) {
    const a = solid(front);
    const b = solid(back);
    if (!a || !b) continue;
    const value = ratio(a, b);
    if (value < needed) problems.push(`  ${front} on ${back}: ${value.toFixed(2)} (needs ${needed}, ${what})`);
  }
  console.log(`${name}: ${problems.length ? problems.length + " below" : "all pass"}`);
  for (const line of problems) console.log(line);
  failures += problems.length;
}
process.exit(failures ? 1 : 0);
