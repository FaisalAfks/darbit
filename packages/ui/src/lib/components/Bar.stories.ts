// Bar in its states. Theme and backdrop: the toolbar at the top.
import type { Meta, StoryObj } from "@storybook/svelte-vite";
import Bar from "./Bar.svelte";

const meta = { title: "Progress/Bar", component: Bar } satisfies Meta<typeof Bar>;
export default meta;
type Story = StoryObj<typeof meta>;

export const Empty: Story = { args: {"label": "Raid Challenge today", "done": 0, "total": 1} };
export const Full: Story = { args: {"label": "Boss Rush today", "done": 1, "total": 1} };
