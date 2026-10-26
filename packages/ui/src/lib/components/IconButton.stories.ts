// IconButton in its states. Theme and backdrop: the toolbar at the top.
import type { Meta, StoryObj } from "@storybook/svelte-vite";
import IconButton from "./IconButton.svelte";

const meta = { title: "Basics/IconButton", component: IconButton } satisfies Meta<typeof IconButton>;
export default meta;
type Story = StoryObj<typeof meta>;

export const Pause: Story = { args: {"label": "Pause", "icon": "❚❚"} };
export const ToggleOn: Story = { args: {"label": "Snapping", "icon": "⌗", "pressed": true} };
