// StatusList in its states. Theme and backdrop: the toolbar at the top.
import type { Meta, StoryObj } from "@storybook/svelte-vite";
import StatusList from "./StatusList.svelte";

const meta = { title: "Studio/StatusList", component: StatusList } satisfies Meta<typeof StatusList>;
export default meta;
type Story = StoryObj<typeof meta>;

export const Watching: Story = { args: {"label": "Watching", "items": [{"name": "Disconnected", "detail": "fired 0 times today", "status": "ok", "chip": {"text": "watching", "tone": "ok"}}, {"name": "Roblox closed", "detail": "fired once, 08:41 · rejoined", "status": "ok", "chip": {"text": "watching", "tone": "ok"}}]} };
export const Round: Story = { args: {"label": "Today's round", "items": [{"name": "Raid", "detail": "11:02 · 41 m", "status": "ok", "chip": {"text": "done", "tone": "ok"}}, {"name": "Speed Raid", "detail": "11:24 · now", "status": "now", "chip": {"text": "running", "tone": "info"}}, {"name": "Raid Challenge", "detail": "next in this round", "status": "idle"}, {"name": "AFK", "detail": "09:12 · failed", "status": "bad", "chip": {"text": "no rewards", "tone": "danger"}}]} };
