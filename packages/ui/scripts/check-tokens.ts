// Fails when a theme misses a colour token from the design system's table, or tokens.css misses one of
// the theme-independent ones. Run by `npm run check`. Spec: docs/style/ui/design-system.md (Tokens).
import { readdirSync, readFileSync } from "node:fs";

const here = new URL(".", import.meta.url);
const spec = readFileSync(new URL("../../../docs/style/ui/design-system.md", here), "utf8");
const themes = readFileSync(new URL("../src/lib/tokens/themes.css", here), "utf8");
const shared = readFileSync(new URL("../src/lib/tokens/tokens.css", here), "utf8");

// rows of the Tokens table whose tokens change per theme; the rest live in tokens.css
const COLOUR_GROUPS = ["Surfaces", "Text", "Accent", "Status", "Target kinds", "Text slots"];

function tokensIn(text: string): string[] {
  const found: string[] = [];
  for (const match of text.matchAll(/`(--[a-z0-9-]+)`/g)) {
    if (!found.includes(match[1])) found.push(match[1]);
  }
  return found;
}

function defined(block: string): Set<string> {
  const names = new Set<string>();
  for (const match of block.matchAll(/(--[a-z0-9-]+)\s*:/g)) names.add(match[1]);
  return names;
}

const colour: string[] = [];
const other: string[] = [];
for (const line of spec.split("\n")) {
  const row = line.match(/^\| ([A-Za-z ]+) \| (.+) \|$/);
  if (!row) continue;
  const tokens = tokensIn(row[2]);
  if (COLOUR_GROUPS.includes(row[1].trim())) colour.push(...tokens);
  else other.push(...tokens);
}
const shared_expected: string[] = [];
for (const token of other) shared_expected.push(token);

const problems: string[] = [];
if (colour.length < 20) problems.push(`only ${colour.length} colour tokens read from the design system: is the table there?`);
const blocks = [...themes.matchAll(/((?::root,\s*)?\[data-theme="([a-z-]+)"\])\s*\{([^}]*)\}/g)];
if (blocks.length === 0) problems.push("no [data-theme] blocks in themes.css");
for (const block of blocks) {
  const names = defined(block[3]);
  for (const token of colour) {
    if (!names.has(token)) problems.push(`theme ${block[2]} misses ${token}`);
  }
}
const sharedNames = defined(shared);
for (const token of shared_expected) {
  if (!sharedNames.has(token)) problems.push(`tokens.css misses ${token}`);
}

// no colours outside the token files: components use tokens, and mix tints with color-mix()
function filesUnder(folder: URL): URL[] {
  const files: URL[] = [];
  for (const entry of readdirSync(folder, { withFileTypes: true })) {
    if (entry.isDirectory()) files.push(...filesUnder(new URL(`${entry.name}/`, folder)));
    else if (/\.(svelte|css|ts)$/.test(entry.name)) files.push(new URL(entry.name, folder));
  }
  return files;
}
const tokenFolder = new URL("../src/lib/tokens/", here).href;
for (const file of filesUnder(new URL("../src/", here))) {
  if (file.href.startsWith(tokenFolder)) continue;
  const lines = readFileSync(file, "utf8").split("\n");
  lines.forEach((line, index) => {
    if (/#[0-9a-fA-F]{3,8}\b|rgba?\(|hsla?\(/.test(line)) {
      problems.push(`${file.pathname.split("/src/")[1]}:${index + 1}: a colour outside the token files`);
    }
  });
}

// no raw pixel sizes in components: they use the scales. Allowed: 1-2 px hairlines and offsets, media
// queries, and a component's own named sizes (a line that declares `--name: 44px`).
const RAW_PX = /(?<![\w.-])(\d+(?:\.\d+)?)px/g;
for (const file of filesUnder(new URL("../src/", here))) {
  if (file.href.startsWith(tokenFolder) || !/\.(svelte|css)$/.test(file.pathname)) continue;
  let text = readFileSync(file, "utf8");
  if (file.pathname.endsWith(".svelte")) {
    const style = text.indexOf("<style>");
    if (style < 0) continue;
    text = text.slice(style);
  }
  text.split("\n").forEach((line, index) => {
    if (/^\s*--[a-z0-9-]+\s*:/.test(line) || line.includes("@media")) return;
    for (const match of line.matchAll(RAW_PX)) {
      if (Number(match[1]) > 2) {
        problems.push(`${file.pathname.split("/src/")[1]}: ${match[0]} in a style; use a token (docs/style/ui/design-system.md)`);
      }
    }
  });
}

if (problems.length) {
  console.error(problems.join("\n"));
  process.exit(1);
}
console.log(`tokens: ${blocks.length} themes × ${colour.length} colour tokens, ${shared_expected.length} shared, all there`);
