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
  /** grab and send frames, then lines */
  "capture.freeze": { monitors: number[] | null };
  /** boxes around a point, smallest first */
  "capture.candidates": { x: number; y: number; kind: Kind };
  /** the project's saved targets */
  "capture.targets": Record<string, never>;
  /** write the target's files */
  "capture.save": { draft: Draft };
  /** undo the last save, rename or delete */
  "capture.undo": Record<string, never>;
  /** redo it */
  "capture.redo": Record<string, never>;
  /** rename a target's files and links */
  "capture.rename": { from: string; to: string };
  /** delete a target's files */
  "capture.delete": { name: string };
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
  /** days with a run report */
  "reports.days": { path: string };
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
  /** snap lines for a frozen frame */
  "capture.lines": { monitor: number; lines: Lines };
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
}

export type RequestType = keyof Requests;
export type EventType = keyof Events;
