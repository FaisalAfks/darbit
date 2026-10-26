// Switch in its states. Theme and backdrop: the toolbar at the top.
import type { Meta, StoryObj } from "@storybook/svelte-vite";
import Switch from "./Switch.svelte";

const meta = { title: "Controls/Switch", component: Switch } satisfies Meta<typeof Switch>;
export default meta;
type Story = StoryObj<typeof meta>;

export const On: Story = { args: {"label": "Speed Raid", "help": "The next character, every 30 minutes.", "checked": true} };
export const Off: Story = { args: {"label": "AFK", "help": "Claim the AFK rewards.", "checked": false} };
