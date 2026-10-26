// Generated from packages/darbit/src/darbit/server/protocol.py; don't edit by hand:
//   uv run python -m darbit.server.protocol --ts > packages/ui/src/lib/protocol.ts

export type Keymap = Record<string, Record<string, string>>;
export type Kind = "image" | "region" | "point";
export type Box = { x: number; y: number; w: number; h: number };
export type Lines = { h: [number, number, number][]; v: [number, number, number][] };
export type Draft = Record<string, unknown>;

export interface Requests {
  /** is the server there */
  "ping": Record<string, never>;
  /** the merged keymap */
  "keymap.get": Record<string, never>;
  /** the theme name and custom tokens */
  "theme.get": Record<string, never>;
  /** a UI setting */
  "settings.get": { key: string };
  /** save a UI setting */
  "settings.set": { key: string; value: unknown };
  /** hide the Studio, freeze, show Capture */
  "capture.open": { path: string; mode: string; name: string | null; kind: Kind | null };
  /** the items still to take */
  "capture.session": Record<string, never>;
  /** the frozen shot as a frame */
  "capture.frame": Record<string, never>;
  /** boxes around a point, smallest first */
  "capture.candidates": { x: number; y: number; kind: Kind };
  /** every match in the region, with scores */
  "capture.test": { box: Box | null; name: string | null; region: Box | null; similarity: number };
  /** write the target's files */
  "capture.save": { name: string; kind: Kind; image: Box | null; region: Box | null; point: number[] | null };
  /** leave Capture and show the Studio */
  "capture.close": Record<string, never>;
  /** hide Capture until the next guide screen is frozen */
  "capture.next": Record<string, never>;
  /** grab the screen again */
  "capture.refreeze": Record<string, never>;
  /** start a scan */
  "highlight.scan": { targets: string[] | null; context: string | null };
  /** show the guide card */
  "guide.open": { path: string; say: string | null; only: string[] | null };
  /** start recording */
  "record.start": { name: string; window: string };
  /** add a checkpoint */
  "record.mark": Record<string, never>;
  /** pause or resume recording */
  "record.pause": Record<string, never>;
  /** stop and save */
  "record.stop": Record<string, never>;
  /** the run's tree */
  "run.load": { path: string };
  /** drive the player */
  "run.control": { do: "continue" | "stop" | "step" | "pause" };
  /** change, add or remove a step */
  "run.edit": { at: number[]; step: Record<string, unknown> };
  /** installed bots and added project folders */
  "projects.list": Record<string, never>;
  /** add a project folder */
  "project.add": { path: string };
  /** start a bot */
  "project.run": { path: string };
  /** pause or resume a bot */
  "project.pause": { path: string };
  /** stop a bot */
  "project.stop": { path: string };
  /** a bot's Overview tiles */
  "dashboard.tiles": { path: string; day: string | null };
  /** a bot's settings form and values */
  "project.settings": { path: string };
  /** save a bot's settings */
  "project.settings.save": { path: string; values: Record<string, unknown> };
  /** pictures with thumbnails and last scores */
  "library.list": { path: string };
  /** every line in the bot that names an asset */
  "library.uses": { path: string; name: string };
  /** what renaming an asset would change */
  "library.rename.plan": { path: string; name: string; to: string };
  /** rename an asset and every line naming it */
  "library.rename": { path: string; name: string; to: string };
  /** the Results page's days, each with its lead gain */
  "results.days": { path: string };
  /** one day of the Results page */
  "results.day": { path: string; day: string | null };
  /** open capture, guide or check for a bot */
  "tools.open": { path: string; tool: string };
  /** hide the Studio behind the run pill while the bot runs */
  "studio.collapse": { path: string };
  /** bring the Studio back from the run pill */
  "studio.expand": Record<string, never>;
}

export interface Events {
  /** the keymap was edited */
  "keymap.changed": { keys: Keymap };
  /** every window switches */
  "theme.changed": { name: string; tokens: Record<string, unknown> | null };
  /** a log line from a running script */
  "log": { line: string; time: string };
  /** a run report event (steps, searches) */
  "record": { event: string; fields: Record<string, unknown> };
  /** a new shot is ready */
  "capture.frozen": Record<string, never>;
  /** the bar between guide items is showing again */
  "capture.waiting": Record<string, never>;
  /** one target found */
  "highlight.hit": { name: string; box: Box; score: number; elsewhere: number; verdict: string };
  /** the scan finished */
  "highlight.done": { missing: string[] };
  /** guide progress */
  "guide.progress": { done: number; total: number; current: string | null };
  /** the bar's clock */
  "record.tick": { seconds: number; checkpoints: number; paused: boolean };
  /** the step being played */
  "run.at": { checkpoint: number; goal: number; step: number };
  /** stopped at a breakpoint or by pause */
  "run.paused": { reason: string };
  /** a bot started, paused or ended */
  "project.status": { path: string; status: string; code: number | null };
  /** a running bot's report changed */
  "project.changed": { path: string };
  /** the tray asks the Studio to show a page (studio-settings) */
  "studio.page": { page: string };
}

export type RequestType = keyof Requests;
export type EventType = keyof Events;
