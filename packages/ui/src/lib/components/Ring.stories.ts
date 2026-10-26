// Ring in its states. Theme and backdrop: the toolbar at the top.
import type { Meta, StoryObj } from "@storybook/svelte-vite";
import Ring from "./Ring.svelte";

const meta = { title: "Progress/Ring", component: Ring } satisfies Meta<typeof Ring>;
export default meta;
type Story = StoryObj<typeof meta>;

export const SpeedRaidWeek: Story = { args: {"label": "Speed Raid this week", "done": 32, "total": 133} };
export const Done: Story = { args: {"label": "Setup", "done": 165, "total": 165} };
